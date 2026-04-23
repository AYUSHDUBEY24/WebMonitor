import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


LOG_PATH = Path("logs/uptime_log.csv")
REPORT_PATH = Path("logs/daily_report.md")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def generate_report(log_path: Path = LOG_PATH, report_path: Path = REPORT_PATH) -> None:
    if not log_path.exists():
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Daily Uptime Report\n\nNo data available.\n", encoding="utf-8")
        return

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=1)

    rows = []
    with log_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                ts = parse_timestamp(row["timestamp_utc"])
            except Exception:  # noqa: BLE001
                continue
            row["_ts"] = ts
            rows.append(row)

    last_24h = [r for r in rows if r["_ts"] >= since]
    grouped = defaultdict(list)
    for row in last_24h:
        grouped[row["name"]].append(row)

    lines = ["# Daily Uptime Report", "", f"Generated (UTC): {now.isoformat()}", ""]
    lines.append("## Last 24 Hours Summary")
    lines.append("")

    if not grouped:
        lines.append("No checks found in the last 24 hours.")
    else:
        lines.append("| Service | Checks | Uptime % | Avg Latency (ms) | Last Status |")
        lines.append("|---|---:|---:|---:|---|")
        for name in sorted(grouped.keys()):
            service_rows = grouped[name]
            checks = len(service_rows)
            up_count = sum(1 for r in service_rows if r["is_up"] == "1")
            uptime_pct = (up_count / checks) * 100 if checks else 0
            latencies = [int(r["latency_ms"]) for r in service_rows if r["latency_ms"].isdigit()]
            avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
            last = sorted(service_rows, key=lambda r: r["_ts"])[-1]
            last_status = "UP" if last["is_up"] == "1" else "DOWN"
            lines.append(
                f"| {name} | {checks} | {uptime_pct:.2f} | {avg_latency} | {last_status} |"
            )

    lines.extend(["", "## Latest Raw Entries", "", "| Time (UTC) | Service | Status | Latency (ms) | Error |", "|---|---|---|---:|---|"])
    latest = sorted(rows, key=lambda r: r["_ts"], reverse=True)[:10]
    for row in latest:
        status = "UP" if row["is_up"] == "1" else "DOWN"
        error = row["error"].replace("|", "/")
        lines.append(f"| {row['timestamp_utc']} | {row['name']} | {status} | {row['latency_ms']} | {error} |")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate_report()
    print(f"Report generated at {REPORT_PATH}")
