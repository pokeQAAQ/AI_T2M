#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI音乐生成应用测试脚本
验证核心功能模块的正确性
"""

import sys
import os
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config():
    """测试配置模块"""
    try:
        from config import get_app_config, get_music_config, ACCESS_KEY, SECRET_KEY
        
        app_config = get_app_config()
        music_config = get_music_config()
        
        logger.info("✅ 配置模块测试通过")
        logger.info(f"窗口尺寸: {app_config.WINDOW_WIDTH}x{app_config.WINDOW_HEIGHT}")
        logger.info(f"音乐风格数量: {len(music_config.GENRES)}")
        logger.info(f"情绪选项数量: {len(music_config.MOODS)}")
        logger.info(f"API主机: {music_config.HOST}")
        
        # 验证凭据
        assert ACCESS_KEY, "ACCESS_KEY不能为空"
        assert SECRET_KEY, "SECRET_KEY不能为空"
        logger.info("✅ API凭据验证通过")
        
        return True
    except Exception as e:
        logger.error(f"❌ 配置模块测试失败: {e}")
        return False

def test_sign_module():
    """测试签名模块"""
    try:
        from music.sign import hash_sha256, get_x_date, create_request_headers
        
        # 测试哈希函数
        test_string = "Hello, World!"
        hash_result = hash_sha256(test_string)
        assert len(hash_result) == 64, "SHA256哈希长度应为64"
        
        # 测试时间戳生成
        timestamp = get_x_date()
        assert len(timestamp) == 16, "时间戳格式不正确"
        assert timestamp.endswith('Z'), "时间戳应以Z结尾"
        
        logger.info("✅ 签名模块测试通过")
        logger.info(f"测试哈希: {hash_result[:32]}...")
        logger.info(f"时间戳: {timestamp}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 签名模块测试失败: {e}")
        return False

def test_music_generator():
    """测试音乐生成模块"""
    try:
        from music.generator import MusicAPIClient
        
        # 创建客户端实例
        client = MusicAPIClient()
        
        # 验证配置
        assert client.access_key, "访问密钥不能为空"
        assert client.secret_key, "秘密密钥不能为空"
        assert client.music_config.HOST, "API主机不能为空"
        
        logger.info("✅ 音乐生成模块测试通过")
        logger.info(f"API主机: {client.music_config.HOST}")
        logger.info(f"API版本: {client.music_config.VERSION}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 音乐生成模块测试失败: {e}")
        return False

def test_existing_threads():
    """测试现有的线程模块"""
    try:
        # 测试录音线程（不实际运行）
        from threads.record_thread import RecordThread
        
        # 创建实例但不启动
        record_thread = RecordThread("/tmp/test_record.wav")
        assert record_thread.rate == 16000, "采样率应为16000"
        assert record_thread.channels == 1, "声道数应为1"
        
        logger.info("✅ 录音线程模块测试通过")
        
        # 测试ASR线程（不实际运行）
        from threads.asr_thread import ASRThread
        
        # 创建实例但不启动
        asr_thread = ASRThread("/tmp/test_audio.wav")
        
        logger.info("✅ ASR线程模块测试通过")
        
        return True
    except Exception as e:
        logger.error(f"❌ 线程模块测试失败: {e}")
        return False

def test_api_request_format():
    """测试API请求格式"""
    try:
        from music.sign import prepare_request_data, create_request_headers
        from config import ACCESS_KEY, SECRET_KEY, get_music_config
        
        # 测试数据
        test_data = {
            "prompt": "写一首关于春天的歌",
            "gender": "Female",
            "genre": "Pop",
            "mood": "Happy"
        }
        
        # 准备请求数据
        body_str = prepare_request_data(test_data)
        json_data = json.loads(body_str)
        
        assert json_data["prompt"] == test_data["prompt"]
        assert json_data["gender"] == test_data["gender"]
        
        # 生成请求头
        config = get_music_config()
        headers = create_request_headers(
            ACCESS_KEY, SECRET_KEY, "POST",
            config.HOST, body_str,
            config.GEN_SONG_ACTION, config.VERSION, config.REGION
        )
        
        assert "Authorization" in headers
        assert "X-Date" in headers
        assert "X-Content-Sha256" in headers
        assert headers["Content-Type"] == "application/json"
        
        logger.info("✅ API请求格式测试通过")
        logger.info(f"请求体: {body_str}")
        logger.info(f"Authorization头长度: {len(headers['Authorization'])}")
        
        return True
    except Exception as e:
        logger.error(f"❌ API请求格式测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("🧪 开始运行AI音乐生成应用测试...")
    
    tests = [
        ("配置模块", test_config),
        ("签名模块", test_sign_module),
        ("音乐生成模块", test_music_generator),
        ("现有线程模块", test_existing_threads),
        ("API请求格式", test_api_request_format)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 测试 {test_name}...")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} 测试通过")
        else:
            logger.error(f"❌ {test_name} 测试失败")
    
    logger.info(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！应用核心功能正常")
        return True
    else:
        logger.error(f"⚠️ {total - passed} 个测试失败，请检查相关模块")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)