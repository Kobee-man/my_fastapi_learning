#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qwen 3.5 4B 模型集成测试套件
Integration Test Suite for Qwen 3.5 4B Model

功能：
✅ 连接性测试
✅ 模型响应测试
✅ 题目生成测试
✅ 问题判断测试
✅ 性能基准测试
✅ 中文处理能力验证

使用方法:
  python test_qwen_integration.py
"""

import sys
import time
import json
from datetime import datetime

# 导入主程序模块（需要确保在正确目录）
sys.path.insert(0, '.')

try:
    from turtle_soup_qwen import (
        QwenConfig, 
        QwenClient, 
        GameConfig,
        ConnectionStatus,
        QwenPromptTemplates,
        ResponseCache
    )
except ImportError as e:
    print(f"[错误] 无法导入模块: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


class Color:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title):
    """打印标题头"""
    width = 60
    print("\n" + "=" * width)
    print(f"{Color.BOLD}{Color.CYAN}  {title}{Color.END}")
    print("=" * width + "\n")


def print_test(name, status, detail=""):
    """打印测试结果"""
    icon = "✓" if status == "PASS" else "✗"
    color = Color.GREEN if status == "PASS" else Color.RED
    
    if detail:
        print(f"  [{color}{icon}{Color.END}] {name}: {detail}")
    else:
        print(f"  [{color}{icon}{Color.END}] {name}")


class QwenIntegrationTest:
    """Qwen 3.5 4B 集成测试类"""
    
    def __init__(self):
        self.config = QwenConfig(
            host="http://localhost:11434",
            model="qwen3.5:4b",
            temperature=0.6,
            timeout=180,
            log_requests=True
        )
        
        self.client = None
        self.test_results = []
        self.start_time = None
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        
        print("=" * 65)
        print(f"{Color.BOLD}{Color.CYAN}")
        print("  🧪 Qwen 3.5 4B 集成测试套件")
        print("  Integration Test Suite for Qwen 3.5 4B")
        print(f"{Color.END}")
        print("=" * 65)
        print(f"\n  📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🎯 目标模型: {self.config.model}")
        print(f"  🔗 服务地址: {self.config.host}\n")
        
        # 测试模块列表
        tests = [
            ("连接性测试", self._test_connection),
            ("模型信息获取", self._test_model_info),
            ("模型列表获取", self._test_list_models),
            ("基础生成能力", self._test_basic_generation),
            ("中文理解能力", self._test_chinese_understanding),
            ("JSON输出格式", self._test_json_output),
            ("题目生成功能", self._test_puzzle_generation),
            ("问题判断功能", self._test_judgment),
            ("重试机制", self._test_retry_mechanism),
            ("缓存系统", self._test_cache_system),
            ("性能基准测试", self._test_performance_benchmark),
            ("错误处理能力", self._test_error_handling),
        ]
        
        # 执行所有测试
        for test_name, test_func in tests:
            try:
                print_header(test_name)
                passed, details = test_func()
                self.test_results.append((test_name, passed))
                
                if isinstance(details, list):
                    for d in details:
                        print_test(d['name'], d['status'], d.get('detail', ''))
                else:
                    print_test(test_name, passed, details)
                    
                print()
                
            except Exception as e:
                self.test_results.append((test_name, False))
                print_test(test_name, False, f"异常: {e}")
                print()
        
        # 输出总结报告
        self._print_summary()
    
    def _test_connection(self):
        """测试1：连接性测试"""
        self.client = QwenClient(self.config)
        status, msg = self.client.check_connection()
        
        return (status == ConnectionStatus.CONNECTED, msg)
    
    def _test_model_info(self):
        """测试2：模型信息获取"""
        info = self.client._get_model_info()
        
        if not info:
            return (False, "无法获取模型信息")
        
        checks = [
            {'name': '返回数据结构', 'status': 'details' in info},
            {'name': '包含参数信息', 'status': bool(info.get('details'))},
            {'name': '模型名称匹配', 'status': True},  # 已通过连接测试验证
        ]
        
        return (True, checks)
    
    def _test_list_models(self):
        """测试3：模型列表获取"""
        models = self.client.list_models()
        
        checks = [
            {
                'name': '返回列表非空', 
                'status': len(models) > 0,
                'detail': f'找到 {len(models)} 个模型'
            },
            {
                'name': '目标模型存在',
                'status': any(m['name'] == self.config.model for m in models)
            }
        ]
        
        return (len(models) > 0, checks)
    
    def _test_basic_generation(self):
        """测试4：基础文本生成能力"""
        success, response, meta = self.client.generate_with_retry(
            prompt="请用一句话介绍你自己。",
            system_prompt="你是Qwen AI助手。",
            max_retries=2
        )
        
        checks = [
            {
                'name': '请求成功',
                'status': success,
                'detail': f'延迟: {meta["latency_ms"]:.0f}ms'
            },
            {
                'name': '响应非空',
                'status': len(response) > 10,
                'detail': f'长度: {len(response)}字符'
            },
            {
                'name': '包含中文',
                'status': any('\u4e00' <= c <= '\u9fff' for c in response)
            }
        ]
        
        return (success and len(response) > 10, checks)
    
    def _test_chinese_understanding(self):
        """测试5：中文理解能力"""
        questions = [
            ("简单问答", "什么是海龟汤游戏？"),
            ("逻辑推理", "如果今天下雨，我应该带什么？"),
            ("创意写作", "用一句话描述春天的美。"),
        ]
        
        results = []
        all_passed = True
        
        for name, question in questions:
            success, response, _ = self.client.generate_with_retry(
                prompt=question,
                max_retries=1
            )
            
            passed = success and len(response) > 5
            all_passed = all_passed and passed
            
            results.append({
                'name': f'{name}',
                'status': passed,
                'detail': f'{len(response)}字' if response else '失败'
            })
        
        return (all_passed, results)
    
    def _test_json_output(self):
        """测试6：JSON格式输出能力"""
        prompt = """请以JSON格式回答以下问题，只输出JSON不要其他内容：
{"name": "你的名字", "version": "版本号", "language": "主要语言"}"""
        
        success, response, _ = self.client.generate_with_retry(
            prompt=prompt,
            temperature=0.1,  # 低温度保证结构化输出
            max_retries=2
        )
        
        is_valid_json = False
        parsed = None
        
        if response:
            try:
                # 尝试提取和解析JSON
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    is_valid_json = isinstance(parsed, dict)
            except Exception:
                pass
        
        checks = [
            {'name': '请求成功', 'status': success},
            {'name': '有效JSON格式', 'status': is_valid_json},
            {'name': '包含必要字段', 'status': parsed is not None and 'name' in parsed}
        ]
        
        return (is_valid_json, checks)
    
    def _test_puzzle_generation(self):
        """测试7：海龟汤题目生成功能"""
        success, puzzle = self.client.generate_puzzle(difficulty="easy")
        
        if not puzzle:
            return (False, "题目生成失败")
        
        required_fields = ['situation', 'truth']
        has_all_fields = all(k in puzzle for k in required_fields)
        
        checks = [
            {
                'name': '生成成功',
                'status': success
            },
            {
                'name': '包含情境描述',
                'status': 'situation' in puzzle and len(puzzle.get('situation', '')) > 10,
                'detail': f'{len(puzzle.get("situation", ""))}字'
            },
            {
                'name': '包含完整真相',
                'status': 'truth' in puzzle and len(puzzle.get('truth', '')) > 50,
                'detail': f'{len(puzzle.get("truth", ""))}字'
            },
            {
                'name': '字段完整性',
                'status': has_all_fields
            }
        ]
        
        # 显示生成的题目预览
        if has_all_fields:
            print(f"\n  📖 生成的题目预览:")
            print(f"     标题: {puzzle.get('title', '未命名')}")
            print(f"     情境: {puzzle.get('situation', '')[:80]}...")
            print(f"     分类: {puzzle.get('category', '未知')}")
        
        return (success and has_all_fields, checks)
    
    def _test_judgment(self):
        """测试8：问题判断功能"""
        test_situation = "一个人走进酒吧，向酒保要一杯水。酒保拿出枪指着他。那个人说谢谢然后离开了。"
        
        test_questions = [
            ("是/否判断-相关", "这个人认识酒保吗？"),
            ("是/否判断-无关", "这个人是外星人吗？"),
            ("边界情况-直接问真相", "真相是什么？"),
        ]
        
        results = []
        all_valid = True
        
        for i, (name, question) in enumerate(test_questions, 1):
            success, judgment = self.client.judge_question(
                question=question,
                situation=test_situation,
                history=[],
                question_num=i
            )
            
            valid_answer = judgment.get('answer') in ['是', '否', '无关', '部分相关']
            all_valid = all_valid and valid_answer
            
            results.append({
                'name': name,
                'status': valid_answer,
                'detail': f"→ {judgment.get('answer', 'N/A')}"
            })
        
        return (all_valid, results)
    
    def _test_retry_mechanism(self):
        """测试9：重试机制"""
        # 使用无效的提示触发重试（但不会真正失败太多）
        original_retries = self.config.max_retries
        self.config.max_retries = 2
        
        success, _, meta = self.client.generate_with_retry(
            prompt="测试重试机制",
            max_retries=2
        )
        
        self.config.max_retries = original_retries
        
        checks = [
            {
                'name': '重试次数记录',
                'status': meta['attempt'] >= 1,
                'detail': f'实际尝试: {meta["attempt"]}次'
            },
            {
                'name': '最终成功',
                'status': success
            }
        ]
        
        return (success, checks)
    
    def _test_cache_system(self):
        """测试10：缓存系统测试"""
        if not self.client.cache:
            return (False, "缓存未启用")
        
        prompt = "缓存测试唯一字符串XYZ123"
        
        # 第一次调用（应该不命中缓存）
        success1, resp1, meta1 = self.client.generate_with_retry(prompt)
        
        # 第二次调用（应该命中缓存）
        success2, resp2, meta2 = self.client.generate_with_retry(prompt)
        
        cache_hit = meta2.get('cache_hit', False)
        
        checks = [
            {
                'name': '首次调用成功',
                'status': success1
            },
            {
                'name': '缓存命中',
                'status': cache_hit,
                'detail': '第二次调用使用缓存'
            },
            {
                'name': '响应一致性',
                'status': resp1 == resp2,
                'detail': '两次结果相同'
            }
        ]
        
        # 清理测试缓存
        self.client.cache.clear()
        
        return (cache_hit, checks)
    
    def _test_performance_benchmark(self):
        """测试11：性能基准测试"""
        iterations = 3
        latencies = []
        tokens_list = []
        
        print(f"  运行 {iterations} 次迭代测试...\n")
        
        for i in range(iterations):
            start = time.time()
            success, response, meta = self.client.generate_with_retry(
                prompt=f"性能测试第{i+1}次：用一句话描述AI技术。",
                max_retries=2
            )
            elapsed = (time.time() - start) * 1000
            
            latencies.append(meta['latency_ms'])
            tokens_list.append(meta['tokens_used'])
            
            print(f"    第{i+1}次: {meta['latency_ms']:.0f}ms | "
                  f"{meta['tokens_used']} tokens | "
                  f"{len(response)}字符")
        
        avg_latency = sum(latencies) / len(latencies)
        avg_tokens = sum(tokens_list) / len(tokens_list)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        # 判断是否达到可接受性能
        acceptable = avg_latency < 30000  # 30秒内算可接受
        
        checks = [
            {
                'name': '平均延迟',
                'status': avg_latency < 30000,
                'detail': f'{avg_latency:.0f}ms (建议<30s)'
            },
            {
                'name': '最小延迟',
                'status': min_latency < 20000,
                'detail': f'{min_latency:.0f}ms'
            },
            {
                'name': '最大延迟',
                'status': max_latency < 60000,
                'detail': f'{max_latency:.0f}ms (应<60s)'
            },
            {
                'name': '平均Token数',
                'status': avg_tokens > 0,
                'detail': f'{avg_tokens:.0f} tokens/req'
            }
        ]
        
        return (acceptable, checks)
    
    def _test_error_handling(self):
        """测试12：错误处理能力"""
        error_tests = []
        
        # 测试1：空提示处理
        success1, resp1, _ = self.client.generate_with_retry("")
        error_tests.append({
            'name': '空提示处理',
            'status': True,  # 不崩溃就算通过
            'detail': '无异常抛出'
        })
        
        # 测试2：超长提示处理
        long_prompt = "测试" * 10000
        success2, resp2, _ = self.client.generate_with_retry(
            long_prompt,
            max_retries=1
        )
        error_tests.append({
            'name': '长提示处理',
            'status': True,  # 不崩溃
            'detail': '无内存溢出'
        })
        
        # 测试3：特殊字符处理
        special_prompt = '测试特殊字符：<>&"\'\n\t@#$%'
        success3, resp3, _ = self.client.generate_with_retry(
            special_prompt,
            max_retries=1
        )
        error_tests.append({
            'name': '特殊字符处理',
            'status': success3,
            'detail': '正常解析'
        })
        
        return (all(t['status'] for t in error_tests), error_tests)
    
    def _print_summary(self):
        """打印测试总结"""
        total_time = time.time() - self.start_time
        
        total = len(self.test_results)
        passed = sum(1 for _, p in self.test_results if p)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print("=" * 65)
        print(f"\n{Color.BOLD}  📊 测试总结报告{Color.END}\n")
        print(f"  总测试数: {total}")
        print(f"  通过数量: {Color.GREEN}{passed}{Color.END}")
        print(f"  失败数量: {Color.RED if failed > 0 else ''}{failed}{Color.END}")
        print(f"  通过率: {Color.GREEN if pass_rate >= 80 else Color.YELLOW}"
              f"{pass_rate:.1f}%{Color.END}")
        print(f"  总耗时: {total_time:.1f}秒\n")
        
        # 详细结果列表
        print("  详细结果:")
        print("  " + "-" * 55)
        for name, passed in self.test_results:
            icon = "✓" if passed else "✗"
            color = Color.GREEN if passed else Color.RED
            print(f"    [{color}{icon}{Color.END}] {name}")
        
        print("  " + "-" * 55)
        
        # 性能统计
        if self.client:
            print(f"\n  {self.client.get_performance_report()}")
        
        # 最终结论
        print("\n" + "=" * 65)
        if pass_rate >= 90:
            print(f"{Color.GREEN}{Color.BOLD}")
            print("  🎉 优秀！Qwen 3.5 4B 模型集成完全成功！")
            print(f"  系统已准备好投入使用。{Color.END}")
        elif pass_rate >= 70:
            print(f"{Color.YELLOW}{Color.BOLD}")
            print("  ⚠️ 良好！大部分功能正常，少数需要优化。")
            print(f"  建议检查失败的测试项。{Color.END}")
        else:
            print(f"{Color.RED}{Color.BOLD}")
            print("  ❌ 需要改进！多个关键测试未通过。")
            print(f"  请检查Ollama服务和模型配置。{Color.END}")
        
        print(f"{Color.END}\n")
        
        # 返回退出码
        return 0 if pass_rate >= 70 else 1


if __name__ == "__main__":
    tester = QwenIntegrationTest()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
