from app.services.extractor import ResumeExtractor
from app.services.text_processor import TextProcessor


def test_extract_basic_fields():
    text = "张三\n电话: 13812345678\n邮箱: test@example.com\n5年工作经验\n本科\n上海"
    data = ResumeExtractor.extract(text)

    assert data.phone == "13812345678"
    assert data.email == "test@example.com"
    assert data.education == "本科"
    assert data.address == "上海"


def test_low_text_quality_for_scanned_pdf():
    assert TextProcessor.low_text_quality(" ")
    assert TextProcessor.low_text_quality("----++++***")
    assert not TextProcessor.low_text_quality("这是一个正常的简历文本，包含多段中文内容和技能描述。")
