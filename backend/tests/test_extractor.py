from app.services.extractor import ResumeExtractor


def test_extract_basic_fields():
    text = "张三\n电话: 13812345678\n邮箱: test@example.com\n5年工作经验\n本科\n上海"
    data = ResumeExtractor.extract(text)

    assert data.phone == "13812345678"
    assert data.email == "test@example.com"
    assert data.education == "本科"
    assert data.address == "上海"
