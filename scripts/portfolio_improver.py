#!/usr/bin/env python3
"""Portfolio improver agent.

Mines the *live* job market that the job-apply-agent is already collecting
(~/job-apply-agent/data/job_queue.json) for in-demand AWS + networking skills,
then:
  - writes market.json  -> rendered as the "In demand right now" section
  - writes data/lab_backlog.md -> proposed new labs for skills not yet covered
  - commits + pushes if anything changed

Designed to run on a schedule (systemd timer / cron) so the portfolio keeps
improving itself as fresh jobs arrive. Deterministic, no API cost.
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
JOB_QUEUE = Path.home() / "job-apply-agent" / "data" / "job_queue.json"
MARKET = ROOT / "market.json"
BACKLOG = ROOT / "data" / "lab_backlog.md"
LABS = ROOT / "labs.json"

# (display name, [match keywords], category). Curated in-demand vocabulary.
SKILLS = [
    # AWS
    ("AWS VPC", ["vpc"], "aws"), ("EC2", ["ec2"], "aws"), ("S3", ["s3"], "aws"),
    ("IAM", ["iam", "identity and access"], "aws"), ("Lambda / Serverless", ["lambda", "serverless"], "aws"),
    ("EKS / Kubernetes", ["eks", "kubernetes", "k8s"], "aws"), ("ECS / Fargate", ["ecs", "fargate"], "aws"),
    ("CloudFormation", ["cloudformation"], "aws"), ("Terraform", ["terraform"], "aws"),
    ("CloudWatch", ["cloudwatch"], "aws"), ("RDS", ["rds", "aurora"], "aws"),
    ("Route 53 / DNS", ["route 53", "route53"], "aws"), ("CloudFront / CDN", ["cloudfront"], "aws"),
    ("Auto Scaling", ["auto scaling", "autoscaling", "asg"], "aws"),
    ("Load Balancing (ALB/ELB)", ["elb", "alb", "load balanc"], "aws"),
    ("Security Groups", ["security group"], "aws"), ("KMS / Encryption", ["kms", "encryption"], "aws"),
    ("GuardDuty / Security", ["guardduty", "security hub"], "aws"),
    ("CI/CD (CodePipeline)", ["ci/cd", "codepipeline", "codebuild", "pipeline"], "aws"),
    ("Systems Manager", ["systems manager", "ssm"], "aws"),
    ("Cost Optimization", ["cost optim", "finops"], "aws"),
    ("Well-Architected", ["well-architected", "well architected"], "aws"),
    ("CloudOps / Monitoring", ["cloudops", "observability", "monitoring"], "aws"),
    # Networking
    ("TCP/IP", ["tcp/ip", "tcp ip"], "net"), ("DNS", ["dns"], "net"), ("DHCP", ["dhcp"], "net"),
    ("VPN", ["vpn"], "net"), ("BGP", ["bgp"], "net"), ("OSPF", ["ospf"], "net"),
    ("VLAN / Switching", ["vlan", "switching", "802.1q"], "net"), ("Subnetting", ["subnet"], "net"),
    ("Firewalls / ACLs", ["firewall", "acl", "nftables", "iptables"], "net"),
    ("SD-WAN", ["sd-wan", "sdwan"], "net"), ("WireGuard / IPsec", ["wireguard", "ipsec"], "net"),
    ("NAT / Routing", ["nat ", "routing", "router"], "net"), ("Load Balancing", ["load balanc"], "net"),
    ("Network Security", ["network security", "zero trust", "zero-trust"], "net"),
    ("Wireshark / Packet Analysis", ["wireshark", "packet captur", "tcpdump"], "net"),
    ("Network Automation", ["network automation", "ansible", "python"], "net"),
    ("SDN", ["sdn", "software-defined"], "net"), ("QoS", ["qos", "quality of service"], "net"),
]


def load_jobs():
    if not JOB_QUEUE.exists():
        return []
    try:
        data = json.loads(JOB_QUEUE.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else list(data.values())


def job_text(job):
    parts = [job.get("title", ""), job.get("matched_terms", ""),
             job.get("salary_text", ""), job.get("source", "")]
    return " ".join(str(p) for p in parts).lower()


# Current-market baseline demand (0-10, 2026 cloud/network hiring). Local job
# signal is blended on top so the ranking adapts as fresh jobs are collected.
BASELINE = {
    "Terraform": 9, "EKS / Kubernetes": 9, "IAM": 8, "Lambda / Serverless": 8,
    "AWS VPC": 8, "EC2": 7, "S3": 7, "CI/CD (CodePipeline)": 8, "CloudWatch": 7,
    "ECS / Fargate": 7, "Security Groups": 7, "Cost Optimization": 7, "CloudOps / Monitoring": 7,
    "Well-Architected": 6, "RDS": 6, "KMS / Encryption": 6, "GuardDuty / Security": 6,
    "Route 53 / DNS": 6, "Auto Scaling": 6, "Load Balancing (ALB/ELB)": 6, "Systems Manager": 5,
    "CloudFormation": 5, "CloudFront / CDN": 5,
    "Network Security": 9, "DNS": 8, "TCP/IP": 8, "Firewalls / ACLs": 8, "VPN": 8,
    "Network Automation": 8, "DHCP": 7, "Subnetting": 7, "VLAN / Switching": 7, "BGP": 7,
    "WireGuard / IPsec": 6, "NAT / Routing": 6, "SD-WAN": 6, "Wireshark / Packet Analysis": 6,
    "Load Balancing": 6, "OSPF": 5, "Network Security": 8, "SDN": 5, "QoS": 4,
}


def mine(jobs):
    """Blended demand score per skill: market baseline + live local signal."""
    counts = Counter()
    local = {}
    corpus = [job_text(j) for j in jobs]
    for display, keywords, cat in SKILLS:
        c = sum(1 for text in corpus if any(k in text for k in keywords))
        local[display] = c
        score = BASELINE.get(display, 3) + c * 3   # local postings weigh heavily
        counts[(display, cat)] = score
    mine.local = local
    return counts


def covered_skills():
    """Skills already demonstrated by an existing lab (from labs.json)."""
    if not LABS.exists():
        return set()
    try:
        d = json.loads(LABS.read_text(encoding="utf-8"))
    except Exception:
        return set()
    blob = json.dumps(d).lower()
    return {display for (display, kws, cat) in SKILLS if any(k in blob for k in kws)}


def main():
    jobs = load_jobs()
    counts = mine(jobs)
    aws = sorted([(d, n) for (d, c), n in counts.items() if c == "aws"], key=lambda x: -x[1])[:10]
    net = sorted([(d, n) for (d, c), n in counts.items() if c == "net"], key=lambda x: -x[1])[:10]
    top = max([n for _, n in aws + net], default=1)

    def fmt(items):
        return [{"skill": d, "count": mine.local.get(d, 0), "pct": round(100 * n / top)} for d, n in items]

    market = {
        "sampled_jobs": len(jobs),
        "aws": fmt(aws),
        "networking": fmt(net),
    }
    MARKET.write_text(json.dumps(market, indent=2) + "\n", encoding="utf-8")

    # Lab backlog: in-demand skills with no lab covering them yet.
    covered = covered_skills()
    gaps = [(d, n) for d, n in (aws + net) if d not in covered]
    gaps.sort(key=lambda x: -x[1])
    lines = ["# Lab roadmap (auto-generated)", "",
             f"From {len(jobs)} live job postings. In-demand skills not yet covered by a lab:", ""]
    lines += [f"- [ ] **{d}** — seen in {n} postings" for d, n in gaps[:12]] or ["- (all top skills covered 🎉)"]
    BACKLOG.parent.mkdir(parents=True, exist_ok=True)
    BACKLOG.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"market.json: {len(aws)} AWS + {len(net)} networking skills from {len(jobs)} jobs")
    print(f"lab_backlog.md: {len(gaps)} gap skills")

    if "--push" in sys.argv:
        push()


def push():
    changed = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain",
                              "market.json", "data/lab_backlog.md"],
                             capture_output=True, text=True).stdout.strip()
    if not changed:
        print("nothing changed")
        return
    env = {"GH_NO_UPDATE_NOTIFIER": "1"}
    subprocess.run(["git", "-C", str(ROOT), "pull", "--rebase", "--autostash", "-q", "origin", "main"])
    subprocess.run(["git", "-C", str(ROOT), "add", "market.json", "data/lab_backlog.md"])
    subprocess.run(["git", "-C", str(ROOT), "commit", "-q", "-m",
                    "chore(agent): refresh in-demand skills from live job market"])
    r = subprocess.run(["git", "-C", str(ROOT), "push", "origin", "main"], capture_output=True, text=True)
    print("pushed" if r.returncode == 0 else f"push failed: {r.stderr[-200:]}")


if __name__ == "__main__":
    main()
