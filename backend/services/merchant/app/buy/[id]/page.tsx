"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { products } from "@/lib/products";
import { useEffect, useState } from "react";

const generateTracking = () => {
  const prefix = "LCS";
  const random = Math.floor(Math.random() * 900000000) + 100000000;
  return `${prefix}-${random}`;
};

const trackingNumber = generateTracking();

export default function ProtectedPage() {
  const params = useParams();
  const productId = params.id as string;
  const product = products.find(p => p.id === productId);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center px-4">
      <div className="max-w-lg w-full bg-white border border-gray-200 rounded-lg p-8">
        {/* Success Icon */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-8 h-8 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        {/* Thank You Message */}
        <h1 className="text-2xl font-semibold text-gray-900 text-center mb-2">
          Thank You for Your Purchase!
        </h1>
        <p className="text-gray-600 text-center mb-8">Your order has been confirmed</p>

        {/* Order Details */}
        <div className="border-t border-b border-gray-200 py-6 mb-6 space-y-4">
          <div className="flex justify-between">
            <span className="text-gray-600">Product</span>
            <span className="font-medium text-gray-900">{product?.title || "Item"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Amount Paid</span>
            <span className="font-medium text-gray-900">${product?.price} ETH</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Tracking Number</span>
            <span className="font-mono text-sm font-medium text-gray-900">{trackingNumber}</span>
          </div>
        </div>

        {/* Shipping Info */}
        <p className="text-sm text-gray-600 text-center mb-6">
          You will receive a confirmation email shortly with your tracking details. Your order will
          be shipped within 2-3 business days.
        </p>

        {/* Back to Store Button */}
        <Link href="/">
          <button className="w-full bg-gray-900 text-white py-2.5 px-4 rounded hover:bg-gray-800 transition-colors text-sm font-medium">
            Back to Store
          </button>
        </Link>
      </div>
    </div>
  );
}
