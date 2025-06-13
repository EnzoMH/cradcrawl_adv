#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹페이지 파싱 모듈
홈페이지에서 연락처 정보, 텍스트 내용 등을 추출하는 파싱 함수들
"""

import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import urllib3

# settings.py에서 상수들 임포트 (수정)
from settings import (
    PHONE_EXTRACTION_PATTERNS,
    FAX_EXTRACTION_PATTERNS,
    EMAIL_EXTRACTION_PATTERNS,
    ADDRESS_EXTRACTION_PATTERNS,
    WEBSITE_EXTRACTION_PATTERNS,
    KOREAN_AREA_CODES,
    AREA_CODE_LENGTH_RULES,
    LOGGER_NAMES,
    format_phone_number,
    extract_phone_area_code,
    is_valid_area_code
)

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebPageParser:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAMES["parser"])
        
        # settings.py에서 가져온 패턴들 사용
        self.phone_patterns = PHONE_EXTRACTION_PATTERNS
        self.fax_patterns = FAX_EXTRACTION_PATTERNS
        self.email_patterns = EMAIL_EXTRACTION_PATTERNS
        self.address_patterns = ADDRESS_EXTRACTION_PATTERNS
        self.website_patterns = WEBSITE_EXTRACTION_PATTERNS
        
    def format_phone_number_safe(self, number_str):
        """전화번호 포맷팅 (충돌 방지용)"""
        return self.format_phone_number(number_str)
        
    # 텍스트에서 연락처 정보 추출
    def extract_contact_info(self, text):
        """텍스트에서 연락처 정보 추출"""
        contact_info = {
            "phones": [],
            "faxes": [],
            "emails": [],
            "addresses": [],
            "websites": []
        }
        
        try:
            # 전화번호 추출
            for pattern in self.phone_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    formatted_phone = self.format_phone_number_safe(match)
                    if formatted_phone and formatted_phone not in contact_info["phones"]:
                        contact_info["phones"].append(formatted_phone)
            
            # 팩스번호 추출
            for pattern in self.fax_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    formatted_fax = self.format_phone_number_safe(match)
                    if formatted_fax and formatted_fax not in contact_info["faxes"]:
                        contact_info["faxes"].append(formatted_fax)
            
            # 이메일 추출
            for pattern in self.email_patterns:
                email_matches = re.findall(pattern, text, re.IGNORECASE)
                for email in email_matches:
                    if email not in contact_info["emails"]:
                        contact_info["emails"].append(email)
            
            # 주소 추출
            for pattern in self.address_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    cleaned_address = self.clean_address(match)
                    if cleaned_address and cleaned_address not in contact_info["addresses"]:
                        contact_info["addresses"].append(cleaned_address)
            
            # 웹사이트 추출
            for pattern in self.website_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    cleaned_website = self.clean_website(match)
                    if cleaned_website and cleaned_website not in contact_info["websites"]:
                        contact_info["websites"].append(cleaned_website)
        
        except Exception as e:
            self.logger.error(f"연락처 정보 추출 중 오류: {e}")
        
        return contact_info
    
    # 전화번호 포맷팅
    def format_phone_number(self, number_str):
        """전화번호 포맷팅 (settings.py 함수 활용)"""
        if not number_str:
            return None
        
        # 숫자만 추출
        number = re.sub(r'[^\d]', '', number_str)
        
        # 길이 검증 (9-11자리)
        if len(number) < 9 or len(number) > 11:
            return None
        
        # 한국 전화번호 체계에 맞는지 확인 (settings 함수 사용)
        area_code = extract_phone_area_code(number)
        if not area_code or not is_valid_area_code(area_code):
            return None
        
        # settings.py의 포맷팅 함수 사용
        return format_phone_number(number, area_code)
    
    # 한국 전화번호 체계 검증
    def is_valid_korean_phone_number(self, number):
        """한국 전화번호 체계 검증 (settings.py 데이터 활용)"""
        # settings.py의 지역번호 데이터 사용
        for area_code in KOREAN_AREA_CODES.keys():
            if number.startswith(area_code):
                return True
        
        return False
    
    # 주소 정리
    def clean_address(self, address):
        """주소 정리"""
        if not address:
            return None
        
        # 불필요한 공백 제거
        cleaned = re.sub(r'\s+', ' ', address.strip())
        
        # 너무 짧은 주소 제외
        if len(cleaned) < 10:
            return None
        
        # 특수문자 정리
        cleaned = re.sub(r'[^\w\s\-.,()가-힣]', '', cleaned)
        
        return cleaned
    
    # 웹사이트 URL 정리
    def clean_website(self, website):
        """웹사이트 URL 정리"""
        if not website:
            return None
        
        # 공백 제거
        cleaned = website.strip()
        
        # http/https 추가
        if not cleaned.startswith(('http://', 'https://')):
            if cleaned.startswith('www.'):
                cleaned = 'http://' + cleaned
            elif '.' in cleaned:
                cleaned = 'http://' + cleaned
        
        # 유효한 URL 형식인지 확인
        if not re.match(r'https?://[^\s]+\.[^\s]+', cleaned):
            return None
        
        return cleaned
    
    # HTML에서 footer 내용 추출
    def extract_footer_content(self, soup):
        """HTML에서 footer 내용 추출"""
        footer_content = []
        
        try:
            # footer 태그 찾기
            footer_elements = soup.find_all(['footer', 'div'], 
                                          class_=re.compile(r'footer|bottom|contact|info', re.I))
            
            for footer in footer_elements:
                text = footer.get_text().strip()
                if text and len(text) > 10:  # 의미있는 내용만
                    footer_content.append(text)
            
            # footer가 없으면 페이지 하단부 추출
            if not footer_content:
                all_text = soup.get_text()
                # 마지막 1000자 정도를 하단부로 간주
                if len(all_text) > 1000:
                    footer_content.append(all_text[-1000:])
        
        except Exception as e:
            self.logger.error(f"Footer 내용 추출 중 오류: {e}")
        
        return "\n".join(footer_content)
    
    # HTML에서 메타 정보 추출
    def extract_meta_info(self, soup):
        """HTML에서 메타 정보 추출"""
        meta_info = {
            "title": "",
            "description": "",
            "keywords": "",
            "author": ""
        }
        
        try:
            # 제목 추출
            title_tag = soup.find('title')
            if title_tag:
                meta_info["title"] = title_tag.get_text().strip()
            
            # 메타 태그들 추출
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', '').lower()
                content = meta.get('content', '')
                
                if name == 'description':
                    meta_info["description"] = content
                elif name == 'keywords':
                    meta_info["keywords"] = content
                elif name == 'author':
                    meta_info["author"] = content
        
        except Exception as e:
            self.logger.error(f"메타 정보 추출 중 오류: {e}")
        
        return meta_info

    # 홈페이지 전체 파싱
    def parse_homepage(self, url, html_content=None):
        """홈페이지 전체 파싱"""
        result = {
            "url": url,
            "meta_info": {},
            "contact_info": {},
            "footer_content": "",
            "all_text": "",
            "status": "success",
            "error": None
        }
        
        try:
            # HTML 내용 가져오기 (제공되지 않은 경우)
            if html_content is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10, verify=False)
                response.encoding = response.apparent_encoding
                html_content = response.text
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 메타 정보 추출
            result["meta_info"] = self.extract_meta_info(soup)
            
            # 전체 텍스트 추출
            all_text = soup.get_text()
            result["all_text"] = all_text
            
            # 연락처 정보 추출
            result["contact_info"] = self.extract_contact_info(all_text)
            
            # Footer 내용 추출
            result["footer_content"] = self.extract_footer_content(soup)
            
            self.logger.info(f"홈페이지 파싱 완료: {url}")
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.logger.error(f"홈페이지 파싱 중 오류: {url}, 오류: {e}")
        
        return result
    
    # 구조화된 데이터 추출
    def extract_structured_data(self, soup):
        """구조화된 데이터 추출 (JSON-LD, 마이크로데이터 등)"""
        structured_data = {}
        
        try:
            # JSON-LD 스크립트 찾기
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # 조직 정보 추출
                        if data.get('@type') in ['Organization', 'LocalBusiness']:
                            if 'telephone' in data:
                                structured_data['phone'] = data['telephone']
                            if 'faxNumber' in data:
                                structured_data['fax'] = data['faxNumber']
                            if 'address' in data:
                                structured_data['address'] = data['address']
                            if 'url' in data:
                                structured_data['website'] = data['url']
                except:
                    continue
        
        except Exception as e:
            self.logger.error(f"구조화된 데이터 추출 중 오류: {e}")
        
        return structured_data

def test_parser():
    """파서 테스트 함수"""
    parser = WebPageParser()
    
    # 테스트 텍스트
    test_text = """
    효성영광교회
    주소: 서울특별시 강남구 테헤란로 123
    전화: 02-1234-5678
    팩스: 02-1234-5679
    이메일: info@church.co.kr
    홈페이지: www.church.co.kr
    """
    
    print("=" * 50)
    print("📋 웹페이지 파서 테스트")
    print("=" * 50)
    
    contact_info = parser.extract_contact_info(test_text)
    
    print("🔍 추출된 연락처 정보:")
    print(f"  📞 전화번호: {contact_info['phones']}")
    print(f"  📠 팩스번호: {contact_info['faxes']}")
    print(f"  📧 이메일: {contact_info['emails']}")
    print(f"  🏠 주소: {contact_info['addresses']}")
    print(f"  🌐 웹사이트: {contact_info['websites']}")
    print("=" * 50)

if __name__ == "__main__":
    test_parser()