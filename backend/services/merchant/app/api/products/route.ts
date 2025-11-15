import { NextResponse } from "next/server";
import { products } from "@/lib/products";

/**
 * Retrieves all available products.
 *
 * @returns - JSON response containing the products array
 */
export async function GET(): Promise<NextResponse> {
  return NextResponse.json(products);
}
