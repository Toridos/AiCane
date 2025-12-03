import sys
import os
import json

def main():
    if len(sys.argv) < 2:
        print('Usage: debug_ocr_inspect.py <image>')
        return
    img = sys.argv[1]
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, repo_root)

    import run_navigation

    print('Running YOLO text detector (ocr_model) on image:', img)
    try:
        res = run_navigation.ocr_model(img)[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            print('YOLO detect returned no boxes')
        else:
            print('YOLO boxes count:', len(boxes))
            for i, (xyxy, cls, conf) in enumerate(zip(boxes.xyxy, boxes.cls, boxes.conf)):
                print(i, 'cls=', int(cls.item()), 'conf=', float(conf.item()), 'xyxy=', xyxy.cpu().numpy())
    except Exception as e:
        print('YOLO detection failed:', e)

    print('\nRunning run_navigation.run_ocr() (YOLO crops -> EasyOCR)')
    try:
        text_positions = run_navigation.run_ocr(img)
        print('run_ocr returned', len(text_positions), 'entries')
        if text_positions:
            print(json.dumps(text_positions, ensure_ascii=False, indent=2))
    except Exception as e:
        print('run_ocr failed:', e)

    print('\nRunning EasyOCR directly on full image')
    try:
        reader = run_navigation.ocr_reader
        ocr_out = reader.readtext(img)
        print('EasyOCR found', len(ocr_out), 'results')
        for det in ocr_out:
            print(det)
    except Exception as e:
        print('EasyOCR failed:', e)

if __name__ == '__main__':
    main()
