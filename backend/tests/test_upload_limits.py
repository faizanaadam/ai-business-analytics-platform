def test_upload_oversize_rejected(client, seeded_db):
    # 30 MB payload of valid long-format rows — must hit the 25 MB cap
    big = "date,metric,value\n" + "\n".join(
        f"2030-01-01,revenue,{i}" for i in range(1_100_000)
    )
    assert len(big) > 25 * 1024 * 1024
    r = client.post("/api/upload", files={"file": ("big.csv", big.encode(), "text/csv")},
                    data={"source_format": "auto"})
    assert r.status_code == 422
    assert "too large" in r.json()["detail"]


def test_upload_oversized_field_422_not_500(client, seeded_db):
    # single unquoted field > csv field limit must 422, not crash with 500
    huge_field = "x" * 200_000
    csv_payload = f"date,metric,value\n2030-01-01,revenue,{huge_field}\n"
    r = client.post("/api/upload", files={"file": ("weird.csv", csv_payload.encode(), "text/csv")},
                    data={"source_format": "auto"})
    assert r.status_code == 422
