
from src.receipt_pipeline import ReceiptPipeline

# localで動かすためのコード。Lambdaではlambda_handlerがエントリーポイントになる。
def main():
    pipeline = ReceiptPipeline(
        processed_dir="pics/processed_pics"
    )

    result = pipeline.run("pics/raw_pics/receipt1.jpg")

    print("===== FINAL RESULT =====")
    for item in result:
        print(item)


if __name__ == "__main__":
    main()