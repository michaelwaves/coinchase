from dotenv import load_dotenv
from fastapi import FastAPI
from x402.fastapi.middleware import require_payment
from x402.types import EIP712Domain, TokenAmount, TokenAsset
import os
from typing import Any, Dict

load_dotenv()

ADDRESS = os.getenv("ADDRESS")

if not ADDRESS:
    raise ValueError("Missing required env vars")

app = FastAPI()

app.middleware("http")(
    require_payment(
        path="/shirt",
        price="$0.001",
        pay_to_address=ADDRESS,
        network="base-sepolia"
    )
)


app.middleware("http")(
    require_payment(
        path="/premium/*",
        price=TokenAmount(
            amount="10000",
             asset=TokenAsset(
                address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
                decimals=6,
                eip712=EIP712Domain(name="USDC", version="2"),
            ),
        ),
        pay_to_address=ADDRESS,
        network="base-sepolia"
    )
)


@app.get("/shirt")
async def get_shirt()-> Dict[str, Any]:
    return {
        "status":200,
        "message":"Shirt Ordered!"
    }


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4021)

