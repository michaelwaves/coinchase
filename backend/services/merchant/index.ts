import { config } from "dotenv";
import express from "express";
import { paymentMiddleware } from "x402-express";
import { facilitator } from "@coinbase/x402";

config();

const payToAddress = process.env.MERCHANT_WALLET_ADDRESS as `0x${string}`;

// The CDP API key ID and secret are required to use the mainnet facilitator
if (
  !payToAddress ||
  !process.env.MERCHANT_CDP_API_KEY_ID ||
  !process.env.MERCHANT_CDP_API_KEY_SECRET
) {
  console.error("Missing required environment variables");
  process.exit(1);
}

const app = express();

const products = [
  {
    id: "shirt",
    title: "Locus Shirt",
    price: 0.001,
  },
  {
    id: "hoodie",
    title: "Locus Hoodie",
    price: 0.002,
  },
];

app.use(
  paymentMiddleware(
    payToAddress,
    products.reduce(
      (acc, product) => {
        acc[`GET /buy/${product.id}`] = {
          price: `$${product.price}`,
          network: "base",
        };

        return acc;
      },
      {} as Record<string, any>
    ),
    facilitator
  )
);

app.get("/buy/:id", (req, res) => {
  const productBought = products.find(
    (product) => product.id === req.params.id
  );
  res.send({
    description: `You bought the ${productBought?.title}!`,
    trackingCode: "312313",
  });
});

app.get("/products", (req, res) => {
  res.send({
    products,
  });
});

app.listen(4021, () => {
  console.log(`Server listening at http://localhost:4021`);
});
