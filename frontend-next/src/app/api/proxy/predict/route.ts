import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // El puerto 8000 es el del FastAPI (backend-ml)
    // En Docker Compose sería http://backend_ml:8000, pero localmente es localhost:8000
    // Usaremos localhost para pruebas locales, o el de docker si NEXT_PUBLIC_ML_URL existe
    const mlUrl = process.env.NEXT_PUBLIC_ML_URL || 'http://127.0.0.1:8000';
    
    const response = await fetch(`${mlUrl}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`ML API Error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to ML backend:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from ML backend' },
      { status: 500 }
    );
  }
}
