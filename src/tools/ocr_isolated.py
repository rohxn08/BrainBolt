import sys
import logging


logging.getLogger("ppocr").setLevel(logging.ERROR)

def run_ocr(image_path):
    try:
        from paddleocr import PaddleOCR
        
        
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        
       
        result = ocr.ocr(image_path, cls=True)
        
     
        full_text = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                full_text.append(text)
        
        
        print(" ".join(full_text))
        
    except Exception as e:
        
        print(f"OCR_ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_isolated.py <image_path>", file=sys.stderr)
        sys.exit(1)
        
    image_path = sys.argv[1]
    run_ocr(image_path)
