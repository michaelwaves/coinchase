import { Address } from "viem";
import { paymentMiddleware } from "x402-next";
import { facilitator } from "@coinbase/x402";
import { products } from "@/lib/products";

const payTo = process.env.PUBLIC_MERCHANT_WALLET_ADDRESS as Address;

export const middleware = paymentMiddleware(
  payTo,
  products.reduce(
    (acc, product) => {
      acc[`/buy/${product.id}`] = {
        price: `$${product.price}`,
        network: "base",
      };

      return acc;
    },
    {} as Record<string, any>,
  ),
  facilitator,
  {
    appName: "Locus Store",
    appLogo:
      "https://media.licdn.com/dms/image/v2/D4E0BAQFdCda6xVBL3g/company-logo_200_200/B4EZoTMxbBKcAI-/0/1761258706952/paywithlocus_logo?e=1764806400&v=beta&t=01rJQ_k8RjyhlQFQ5rnAB72C34H7hbKSyxBjwkZS5pE",
  },
);

// Configure which paths the middleware should run on
export const config = {
  matcher: ["/buy/shirt", "/buy/hoodie"],
};
