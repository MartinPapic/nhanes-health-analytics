import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = "http://127.0.0.1:8081/api/v1/analytics/member3";

  try {
    const res = await fetch(backendUrl, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ error: "Backend failed", status: res.status }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Proxy error Member 3:", error);
    return NextResponse.json({ error: "Could not connect to backend" }, { status: 500 });
  }
}
