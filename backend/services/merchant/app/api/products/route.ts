import { NextResponse } from "next/server";
import { products } from "@/middleware";

export async function GET() {
  return NextResponse.json(products);
}
