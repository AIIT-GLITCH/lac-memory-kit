export async function onRequestPost({ request, env }) {
  const stripe = await import('https://esm.sh/stripe@14.14.0');
  const client = stripe.default(env.STRIPE_SECRET_KEY);

  const { amount, currency } = await request.json();

  const clamped = Math.max(200, Math.min(5000, amount));

  const session = await client.checkout.sessions.create({
    payment_method_types: ['card'],
    line_items: [{
      price_data: {
        currency: currency || 'usd',
        product_data: {
          name: 'LAC Memory Kit v1.0',
          description: '14-tier AI memory system — memory, promotion gates, affect, voice, browser agent',
        },
        unit_amount: clamped,
      },
      quantity: 1,
    }],
    mode: 'payment',
    success_url: `${new URL(request.url).origin}/success.html`,
    cancel_url: `${new URL(request.url).origin}/`,
  });

  return new Response(JSON.stringify({ url: session.url }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
