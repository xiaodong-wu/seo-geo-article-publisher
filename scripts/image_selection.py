#!/usr/bin/env python3
"""Build recent source-image history and compute an auditable article-wide selection."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

WEIGHTS = dict(keyword_product_relevance=.30, identity_clarity=.25,
               image_quality=.15, section_fit=.15, diversity=.15)
POLICY = "fresh-gallery-history-v2"
HISTORY_LIMIT = 20


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path, p.query, ""))


def same_site(url, host):
    p = urlsplit(url)
    return p.scheme == "https" and (p.hostname or "").removeprefix("www.") == host.removeprefix("www.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def explanation(value):
    return isinstance(value, str) and len(value.strip()) >= 20


def publication_time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    # Historical publisher API timestamps are naive Beijing local time.
    return parsed.replace(tzinfo=timezone(timedelta(hours=8))) if parsed.tzinfo is None else parsed


def history_articles(runs_dir, host):
    """Read only publication and image fields; never copy Sheet credentials or raw rows."""
    articles = {}
    gaps = []
    for path in sorted(Path(runs_dir).glob("*/manifest.json")):
        try:
            manifest = read(path)
            for site in manifest.get("sites", []):
                if not isinstance(site, dict) or site.get("tab") != host:
                    continue
                api = site.get("api_result") or {}
                url = site.get("article_url") or api.get("article_url")
                if not url or not same_site(url, host):
                    continue
                # API success, including pending verification, reserves these sources too.
                if site.get("state") not in {"published", "public-verified", "api-success", "pending-manual-check"} and not api.get("article_id"):
                    continue
                ref_path = Path(site.get("image_reference_file") or Path(site.get("row_directory", path.parent)) / "image-references.json")
                if not ref_path.is_absolute():
                    ref_path = path.parent / ref_path
                article = dict(article_url=canonical(url), published_at=api.get("created_at") or site.get("sheet_published_at") or manifest.get("started_at", ""),
                               run_id=manifest.get("run_id", path.parent.name), manifest_file=str(path.resolve()),
                               image_reference_file=str(ref_path.resolve()), images=[])
                try:
                    refs = read(ref_path)
                    pool = {c["candidate_id"]: c for c in refs.get("candidate_pool", [])}
                    for record in [refs.get("thumbnail", {})] + refs.get("body", []):
                        c = pool.get(record.get("candidate_id"), {})
                        urls = record.get("reference_urls", [])
                        product_urls = site.get("selected_product_urls", [])
                        source = {
                            "reference_url": c.get("reference_url") or (urls[0] if urls else ""),
                            "source_sha256": c.get("source_sha256", ""),
                            "perceptual_hash": c.get("perceptual_hash", ""),
                            "product_url": c.get("product_url") or (product_urls[0] if record.get("classification") == "product-present" and len(product_urls) == 1 else ""),
                        }
                        if any(source[k] for k in ("reference_url", "source_sha256", "perceptual_hash")):
                            article["images"].append(source)
                    if not article["images"]:
                        raise ValueError("no source image records")
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    article["history_gap"] = f"Source image evidence unavailable: {type(exc).__name__}"
                # Retries and duplicate manifests for the same public article count once.
                key = canonical(url)
                if key not in articles or len(article["images"]) > len(articles[key]["images"]):
                    articles[key] = article
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            gaps.append({"manifest_file": str(path.resolve()), "reason": type(exc).__name__})
    def order(article):
        try:
            return publication_time(article["published_at"]).timestamp(), article["article_url"]
        except (ValueError, TypeError, AttributeError):
            article["history_gap"] = "Publication timestamp unavailable; recency cannot be established"
            return 0, article["article_url"]
    recent = sorted(articles.values(), key=order, reverse=True)[:HISTORY_LIMIT]
    return recent, gaps


def make_history(runs_dir, host, run_id):
    articles, gaps = history_articles(runs_dir, host)
    return dict(policy=POLICY, site_host=host, run_id=run_id, runs_directory=str(Path(runs_dir).resolve()),
                checked_at=datetime.now(timezone.utc).isoformat(), limit=HISTORY_LIMIT,
                scope="Most recent locally recorded same-site API-success or published articles; live archive review must disclose unrecorded articles.",
                articles=articles, coverage_gaps=gaps)


def same_source(candidate, previous):
    if candidate.get("reference_url") and canonical(candidate["reference_url"]) == canonical(previous.get("reference_url", "")):
        return True
    if candidate.get("source_sha256") and candidate["source_sha256"] == previous.get("source_sha256"):
        return True
    first, second = candidate.get("perceptual_hash", ""), previous.get("perceptual_hash", "")
    return bool(first and second and bin(int(first, 16) ^ int(second, 16)).count("1") <= 6)


def usage(candidate, articles):
    source_uses = product_uses = 0
    latest_source = False
    for index, article in enumerate(articles):
        images = article.get("images", [])
        source_match = any(same_source(candidate, image) for image in images)
        source_uses += source_match
        product_uses += bool(candidate.get("product_url") and any(
            canonical(candidate["product_url"]) == canonical(image.get("product_url", "")) for image in images))
        latest_source |= index == 0 and source_match
    # Deterministic history-based diversity, never a constant supplied by the author.
    score = max(0, 100 - 20 * source_uses - 5 * product_uses - 20 * latest_source)
    return dict(source_article_uses=source_uses, product_article_uses=product_uses,
                used_in_latest_article=latest_source, diversity=score)


def resolve_evidence(row_dir, value):
    require(isinstance(value, str) and bool(value), "Evidence path is required")
    path = Path(value)
    if not path.is_absolute():
        path = row_dir / path
    path = path.resolve()
    require(path.is_file(), f"Evidence file missing: {path}")
    return path


def prepare(value, row_dir, host):
    """Validate the current-run shortlist against every reviewed gallery before scoring."""
    row_dir = row_dir.resolve()
    context = value.get("selection_context", {})
    require(context.get("policy") == POLICY, f"selection_context.policy must be {POLICY}; legacy pools must be rebuilt")
    run_id = context.get("run_id")
    require(run_id == row_dir.parent.name, "selection_context.run_id must identify the current run directory")
    discovery_path = resolve_evidence(row_dir, context.get("product_discovery_file"))
    require(discovery_path.parent == row_dir, "Product discovery must be from this row run")
    require(context.get("product_discovery_sha256") == digest(discovery_path), "Product discovery digest does not match")
    discovery = read(discovery_path)
    require(discovery.get("run_id") == run_id and discovery.get("site_host") == host, "Product discovery run/site mismatch")
    history_path = resolve_evidence(row_dir, context.get("image_history_file"))
    history = read(history_path)
    require(history_path.parent == row_dir and history.get("run_id") == run_id and history.get("site_host") == host, "Image history run/site mismatch")
    runs_dir = row_dir.parent.parent
    require(Path(history.get("runs_directory", "")).resolve() == runs_dir, "History must cover this workspace article-runs directory")
    expected_articles, expected_gaps = history_articles(runs_dir, host)
    require(history.get("limit") == HISTORY_LIMIT and history.get("articles") == expected_articles and history.get("coverage_gaps") == expected_gaps,
            "Image history is stale or incomplete; rebuild it from run manifests")
    archive = context.get("live_archive_review", {})
    require(same_site(archive.get("url", ""), host) and explanation(archive.get("coverage_note")), "Record live archive URL and history coverage/limitations")
    require(archive.get("run_id") == run_id, "Live archive review must belong to this run")
    require(resolve_evidence(row_dir, archive.get("evidence_file")).is_relative_to(row_dir), "Live archive evidence must be from this row run")

    pool = value.get("candidate_pool", [])
    require(isinstance(pool, list) and 1 <= len(pool) <= 8, "Shortlist must contain 1–8 candidates after gallery review")
    candidates = {c["candidate_id"]: c for c in pool}
    require(len(candidates) == len(pool), "Duplicate candidate IDs")
    reviews = context.get("gallery_reviews", [])
    by_page = {g["page_url"]: g for g in reviews}
    require(len(by_page) == len(reviews), "Duplicate gallery review page")
    relevant = {p["url"]: p for p in discovery.get("matches", []) if p.get("relevance") in {"exact-product", "same-product-family"}}
    require(relevant.keys() <= by_page.keys(), "Every relevant discovered product gallery must be reviewed before shortlisting")
    seen_candidates = set()
    eligible_sources = set()
    for page, review in by_page.items():
        require(same_site(page, host) and review.get("run_id") == run_id, "Gallery review must be same-site and current-run")
        evidence = resolve_evidence(row_dir, review.get("evidence_file"))
        require(evidence.is_relative_to(row_dir), "Gallery evidence must be freshly saved inside this row directory")
        require(review.get("inspection_complete") is True, "Incomplete gallery cannot establish source availability")
        listed = review.get("gallery_image_urls", [])
        require(isinstance(listed, list) and len(listed) == len(set(listed)), "Gallery URLs must be a deduplicated array")
        if page in relevant:
            require("gallery_image_urls" in relevant[page], "Discovered product needs an explicit gallery_image_urls inventory")
            require(set(listed) == set(relevant[page]["gallery_image_urls"]), "Gallery review omits discovered product images")
        decisions = review.get("images", [])
        require(len(decisions) == len(listed) and {x["reference_url"] for x in decisions} == set(listed), "Every gallery image needs a recorded disposition")
        for item in decisions:
            url = item["reference_url"]
            require(same_site(url, host) and explanation(item.get("reason")), "Gallery disposition requires same-site source and concrete reason")
            decision = item.get("decision")
            require(decision in {"candidate", "excluded", "duplicate", "shortlisted-out"}, "Invalid gallery image disposition")
            require(isinstance(item.get("eligible_for_product_lock"), bool), "Record product-lock eligibility for every reviewed image")
            require(item.get("topic_relation") in {"primary-topic", "supporting-context", "comparison-only"}, "Every gallery image needs a topic_relation before shortlisting")
            if decision == "duplicate":
                target = candidates.get(item.get("duplicate_of"))
                require(target is not None and same_source(item, target), "Duplicate exclusion needs a retained candidate and matching fingerprint")
                require(item["eligible_for_product_lock"] == target["eligible_for_product_lock"], "Duplicate eligibility must match its retained source")
                require(item["topic_relation"] == target.get("topic_relation"), "Duplicate topic relation must match its retained source")
            elif item["eligible_for_product_lock"]:
                require(decision != "excluded", "Eligible product image cannot be silently excluded")
                if item["topic_relation"] == "primary-topic":
                    eligible_sources.add(canonical(url))
            if decision == "candidate":
                c = candidates.get(item.get("candidate_id"))
                require(c is not None and c["reference_url"] == url and c.get("source_page_url") == page, "Candidate must match its reviewed gallery image")
                require(c["eligible_for_product_lock"] == item["eligible_for_product_lock"], "Candidate eligibility disagrees with gallery review")
                require(c.get("topic_relation") == item["topic_relation"], "Candidate topic relation disagrees with gallery review")
                seen_candidates.add(c["candidate_id"])
    require(seen_candidates == candidates.keys(), "Every candidate must originate in this run's reviewed galleries")
    for c in pool:
        source = resolve_evidence(row_dir, c.get("reference_file"))
        require(source.is_relative_to(row_dir), "Candidate file must be downloaded into this row run, not borrowed from an old pool")
        require(c.get("source_sha256") == digest(source), "Candidate source digest does not match")
        require(c.get("topic_relation") in {"primary-topic", "supporting-context", "comparison-only"}, "Candidate needs an explicit topic_relation")
        require(explanation(c.get("relevance_reason")), "Candidate relevance must be justified against the article topic")
        require(c.get("classification") != "non-product" or c.get("eligible_for_product_lock") is False, "Non-product sources cannot support a product lock")
        if c.get("classification") == "product-present":
            require(c.get("product_url") == c.get("source_page_url") and c["product_url"] in relevant, "Product candidate must link to a currently discovered relevant product")
    primary_products = [c for c in pool if c.get("classification") == "product-present" and c.get("topic_relation") == "primary-topic" and c.get("eligible_for_product_lock")]
    require(bool(primary_products) == bool(eligible_sources), "Usable primary-topic product images cannot all be omitted from the shortlist")
    require(value.get("topic_product_visuals") is bool(primary_products), "topic_product_visuals must match the reviewed primary-topic product candidates")
    require(not primary_products or value.get("site_has_product_visuals") is True, "Primary-topic product images require site_has_product_visuals=true")
    if not primary_products:
        require(explanation(value.get("no_topic_product_visual_reason")), "Explain why no product visual supports the primary topic")
    plan = value.get("selection_plan", {})
    slots = plan.get("slots", [])
    require(2 <= len(slots) <= 6 and len({s["slot"] for s in slots}) == len(slots), "Selection requires unique thumbnail and body slots")
    require([s["slot"] for s in slots] == ["thumbnail"] + [f"body-{i:02d}" for i in range(1, len(slots))], "Slots must be in thumbnail then body upload order")
    matrix = plan.get("candidate_slot_scores", [])
    rows = {(x["slot"], x["candidate_id"]): x for x in matrix}
    require(len(rows) == len(matrix) == len(pool)*len(slots) and set(rows) == {(s["slot"],c) for s in slots for c in candidates}, "Score every candidate for every slot exactly once")
    calculated = {}
    for key, item in rows.items():
        slot, cid = key
        c = candidates[cid]
        require(type(item.get("eligible")) is bool and explanation(item.get("eligibility_reason")), "Each candidate-slot pair needs eligibility and a reason")
        if item["eligible"] and slot == "thumbnail":
            require(c["topic_relation"] != "comparison-only", "Comparison-only product cannot represent the article thumbnail")
            if primary_products:
                require(c in primary_products, "Use a verified primary-topic product for the thumbnail when available")
        if item["eligible"] and c.get("classification") == "product-present":
            require(c.get("eligible_for_product_lock") is True, "Selected product must support a complete identity lock")
        evidence = item.get("score_evidence", {})
        scores = {}
        for field in WEIGHTS:
            if field == "diversity":
                continue
            n = item.get("scores", {}).get(field)
            require(type(n) in (int,float) and math.isfinite(n) and 0 <= n <= 100, f"Invalid score: {field}")
            require(explanation(evidence.get(field)), f"Missing inspected score evidence: {field}")
            scores[field] = n
        history_use = usage(c, history["articles"])
        scores["diversity"] = history_use["diversity"]
        scores["weighted_total"] = round(sum(scores[k]*w for k,w in WEIGHTS.items()), 2)
        calculated[key] = dict(scores=scores, history_usage=history_use)
    return candidates, eligible_sources, rows, calculated, primary_products


def compute_plan(value, row_dir, host):
    candidates, eligible_sources, rows, calculated, primary_products = prepare(value, row_dir, host)
    plan = value["selection_plan"]
    slots = plan["slots"]
    allowed = []
    for slot in slots:
        choices = [cid for cid in sorted(candidates) if rows[slot["slot"],cid]["eligible"]]
        require(choices, f"No relevant candidate for {slot['slot']}")
        # Rotation never trades down to a less relevant image merely for novelty.
        best_relevance = max(calculated[slot["slot"],cid]["scores"]["keyword_product_relevance"] for cid in choices)
        allowed.append([cid for cid in choices if calculated[slot["slot"],cid]["scores"]["keyword_product_relevance"] >= best_relevance-5])
    best = None
    for combination in itertools.product(*allowed):
        counts = {cid: combination.count(cid) for cid in set(combination)}
        repeated = [cid for cid,count in counts.items() if count>1]
        if repeated and not (len(repeated)==1 and counts[repeated[0]]==2 and len(eligible_sources)==1 and candidates[repeated[0]] in primary_products):
            continue
        if primary_products and not any(candidates[cid] in primary_products for cid in combination[1:]):
            continue
        score = round(sum(calculated[s["slot"],cid]["scores"]["weighted_total"] for s,cid in zip(slots,combination)) - 18*bool(repeated), 2)
        if best is None or score>best[0]:
            best = score, combination
    require(best is not None, "No distinct relevant assignment; expand reviewed galleries or revise slot roles")
    matrix = []
    for slot in slots:
        for cid in sorted(candidates):
            item = dict(rows[slot["slot"],cid])
            item.update(calculated[slot["slot"],cid])
            matrix.append(item)
    assignments = []
    for slot,cid in zip(slots,best[1]):
        assignments.append({**slot, "candidate_id":cid, **calculated[slot["slot"],cid],
                            "selection_reason": rows[slot["slot"],cid]["eligibility_reason"]})
    return {**plan, "global_selection_method":"weighted-global-assignment-with-duplicate-penalty",
            "policy":POLICY, "objective_score":best[0], "duplicate_penalty":18,
            "candidate_slot_scores":matrix, "slots":assignments}


def validate_selection_evidence(value, manifest_path, host):
    try:
        expected = compute_plan(value, manifest_path.resolve().parent, host)
        plan = value["selection_plan"]
        for field in ("policy", "objective_score", "duplicate_penalty", "candidate_slot_scores", "slots"):
            require(plan.get(field) == expected[field], f"selection_plan.{field} differs from computed selection; run image_selection.py plan")
        # Eligibility counts come from every audited gallery, including images left out of the shortlist.
        repeated = len({s['candidate_id'] for s in expected['slots']}) < len(expected['slots'])
        if repeated:
            context = value['selection_context']
            discovery = read(resolve_evidence(manifest_path.parent, context['product_discovery_file']))
            require(discovery.get('coverage_status') == 'complete' and not discovery.get('coverage_gaps'),
                    'Single-source exception cannot be established with catalogue access gaps')
        return []
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"Image selection evidence: {exc}"]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest="command",required=True)
    h=subs.add_parser("history")
    h.add_argument("--runs-dir",type=Path,required=True);h.add_argument("--site-host",required=True)
    h.add_argument("--run-id",required=True);h.add_argument("--output",type=Path,required=True)
    p=subs.add_parser("plan")
    p.add_argument("--image-reference-file",type=Path,required=True);p.add_argument("--site-host",required=True)
    args=parser.parse_args()
    if args.command=="history":
        value=make_history(args.runs_dir,args.site_host,args.run_id);dest=args.output
    else:
        dest=args.image_reference_file;value=read(dest)
        value['selection_plan']=compute_plan(value,dest.resolve().parent,args.site_host)
        # Only writes selection metadata; never rewrites image identity/inspection records.
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(dest.resolve()),'policy':POLICY,'articles':len(value.get('articles',[]))}))


if __name__=="__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"error: {exc}")
