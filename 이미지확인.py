from pathlib import Path
required = [
"hero-card-hand.jpg","service-movein.jpg","service-move.jpg","service-shop.jpg",
"service-waste.jpg","v10-cleaning-scope.png","v10-before-after.png"
]
base=Path(__file__).parent/"assets"
missing=[x for x in required if not (base/x).exists()]
if missing:
    print("누락 이미지:", *missing, sep="\n- ")
    raise SystemExit(1)
print("이미지 7개 확인 완료 - 정상")
