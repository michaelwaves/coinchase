import Link from "next/link";
import Image from "next/image";
import WordmarkCondensed from "./assets/x402_wordmark_light.svg";
import { products } from "@/lib/products";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 text-gray-900 flex flex-col">
      <div className="flex-grow">
        {/* Hero Section */}
        <section className="max-w-6xl mx-auto px-4 py-20 lg:py-28">
          <div className="text-center">
            <h1 className="text-3xl font-semibold text-gray-900 mb-16">Locus Store</h1>

            {/* Products Grid - Centered */}
            <div className="flex gap-8 justify-center items-start max-w-4xl mx-auto">
              {products.map(product => (
                <Link
                  key={product.id}
                  href={`/buy/${product.id}`}
                  className="bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors w-72"
                >
                  {/* Product Image */}
                  <div className="h-72 bg-gray-100 flex items-center justify-center border-b border-gray-200 relative overflow-hidden">
                    <Image
                      src={product.image}
                      alt={product.title}
                      width={288}
                      height={288}
                      className="w-full h-full object-cover"
                      priority
                    />
                  </div>

                  {/* Product Details */}
                  <div className="p-6">
                    <h3 className="text-xl font-medium text-gray-900 mb-3">{product.title}</h3>
                    <p className="text-2xl text-gray-00 mb-4">${product.price}</p>
                    <button className="w-full bg-gray-900 text-white py-2.5 px-4 rounded hover:bg-gray-800 transition-colors text-sm font-medium">
                      Buy Now
                    </button>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
