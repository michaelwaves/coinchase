import { Address } from "viem";
import { paymentMiddleware, Network, Resource } from "x402-next";
import { facilitator } from "@coinbase/x402";

const payTo = process.env.PUBLIC_MERCHANT_WALLET_ADDRESS as Address;

export const products = [
  {
    id: "shirt",
    title: "Locus Shirt",
    price: 0.001,
    image:
      "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTA5L3JtMzYzLWIwOC1tb2NrdXAtam9iMTAwMy1sOGVobWoyZy5qcGc.jpg",
  },
  {
    id: "hoodie",
    title: "Locus Hoodie",
    price: 0.002,
    image: "https://i.postimg.cc/TP8gtP2W/Screenshot-2025-11-15-at-1-36-07-PM.png",
  },
];

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
