const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8081";

export async function POST(request) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/webhook/onboard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (err) {
    return Response.json(
      { status: "error", errors: [{ step: "connection", error: err.message || "Failed to reach backend" }] },
      { status: 502 }
    );
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    const data = await response.json();
    return Response.json(data);
  } catch (err) {
    return Response.json({ status: "unreachable", error: err.message }, { status: 502 });
  }
}
