import io
import zipfile
import pytest
from app.services.payment_document_parse import parse_payment_document


@pytest.mark.parametrize('encoding', ['utf-8','utf-16'])
async def test_docx_entity_declarations_rejected_in_every_encoding(encoding):
    xml = '<?xml version="1.0" encoding="'+encoding+'"?><!DOCTYPE doc [<!ENTITY x "EXPANSION">]><doc>&x;</doc>'
    output = io.BytesIO()
    with zipfile.ZipFile(output,'w') as archive:
        archive.writestr('word/document.xml',xml.encode(encoding))
    with pytest.raises(ValueError):
        await parse_payment_document(output.getvalue(),'invoice.docx',None)
