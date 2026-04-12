"""
PPT 生成器测试
"""
import pytest
from pathlib import Path

from core.ppt_generator import PPTGenerator


@pytest.fixture
def ppt_generator():
    """创建 PPT 生成器实例"""
    return PPTGenerator()


@pytest.fixture
def sample_tree():
    """示例部门树结构"""
    return [
        {
            'id': 1,
            'name': '总公司',
            'children': [
                {
                    'id': 2,
                    'name': '技术部',
                    'children': [
                        {'id': 4, 'name': '前端组', 'children': []},
                        {'id': 5, 'name': '后端组', 'children': []}
                    ]
                },
                {
                    'id': 3,
                    'name': '市场部',
                    'children': []
                }
            ]
        }
    ]


@pytest.fixture
def sample_stats():
    """示例员工统计数据"""
    return [
        ('前端组', '技术', 'P5', 3),
        ('前端组', '技术', 'P6', 2),
        ('后端组', '技术', 'P5', 4),
        ('后端组', '技术', 'P7', 1),
        ('市场部', '市场', 'P5', 2),
    ]


class TestPPTGenerator:
    """PPTGenerator 测试"""

    def test_init(self, ppt_generator):
        """测试初始化"""
        assert ppt_generator.prs is None

    def test_generate_creates_file(self, ppt_generator, sample_tree, sample_stats, tmp_path):
        """测试生成 PPT 文件"""
        output_path = tmp_path / "output.pptx"

        success, message = ppt_generator.generate(
            tree=sample_tree,
            stats=sample_stats,
            output_path=str(output_path)
        )

        assert success is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generate_with_empty_tree(self, ppt_generator, tmp_path):
        """测试空树生成"""
        output_path = tmp_path / "empty.pptx"

        success, message = ppt_generator.generate(
            tree=[],
            stats=[],
            output_path=str(output_path)
        )

        # 空树也能生成，只是没有内容
        assert success is True
        assert output_path.exists()

    def test_generate_with_empty_stats(self, ppt_generator, sample_tree, tmp_path):
        """测试无统计数据生成"""
        output_path = tmp_path / "no_stats.pptx"

        success, message = ppt_generator.generate(
            tree=sample_tree,
            stats=[],
            output_path=str(output_path)
        )

        assert success is True
        assert output_path.exists()

    def test_generate_invalid_path(self, ppt_generator, sample_tree, sample_stats):
        """测试无效路径"""
        import platform

        # 使用真正无法写入的路径
        if platform.system() == "Windows":
            # Windows: 使用无效字符或受保护的目录
            invalid_path = "Z:\\nonexistent_drive\\output.pptx"
        else:
            # Unix: 使用不存在的路径
            invalid_path = "/nonexistent_drive/output.pptx"

        success, message = ppt_generator.generate(
            tree=sample_tree,
            stats=sample_stats,
            output_path=invalid_path
        )

        assert success is False
        assert "失败" in message or "不存在" in message

    def test_calculate_positions(self, ppt_generator, sample_tree):
        """测试节点位置计算"""
        positions = ppt_generator._calculate_positions(sample_tree)

        # 检查所有节点都有位置
        assert 1 in positions
        assert 2 in positions
        assert 3 in positions
        assert 4 in positions
        assert 5 in positions

        # 检查位置结构
        for node_id, pos in positions.items():
            assert 'x' in pos
            assert 'y' in pos
            assert 'x_center' in pos
            assert 'y_center' in pos
            assert 'name' in pos
            assert 'level' in pos
            assert 'box_width' in pos

    def test_calculate_positions_hierarchy(self, ppt_generator, sample_tree):
        """测试层级位置关系"""
        positions = ppt_generator._calculate_positions(sample_tree)

        # 根节点在最上层 (y 最小)
        root_y = positions[1]['y']

        # 子节点应该在根节点下方
        assert positions[2]['y'] > root_y
        assert positions[3]['y'] > root_y

        # 孙节点应该在子节点下方
        assert positions[4]['y'] > positions[2]['y']
        assert positions[5]['y'] > positions[2]['y']

    def test_get_level_widths(self, ppt_generator, sample_tree):
        """测试每层宽度计算"""
        widths = ppt_generator._get_level_widths(sample_tree)

        # 第 0 层: 1 个根节点
        assert widths.get(0, 0) == 1

        # 第 1 层: 2 个子节点
        assert widths.get(1, 0) == 2

        # 第 2 层: 2 个孙节点
        assert widths.get(2, 0) == 2

    def test_get_level_widths_empty(self, ppt_generator):
        """测试空树的层级宽度"""
        widths = ppt_generator._get_level_widths([])
        assert widths == {}

    def test_level_colors(self, ppt_generator):
        """测试层级颜色定义"""
        assert len(ppt_generator.LEVEL_COLORS) == 5

        # 检查颜色是 RGBColor 类型
        from pptx.dml.color import RGBColor
        for color in ppt_generator.LEVEL_COLORS:
            assert isinstance(color, RGBColor)

    def test_generate_with_deep_tree(self, ppt_generator, tmp_path):
        """测试深层级树结构"""
        # 创建 5 层深的树
        deep_tree = [{
            'id': 1,
            'name': 'L1',
            'children': [{
                'id': 2,
                'name': 'L2',
                'children': [{
                    'id': 3,
                    'name': 'L3',
                    'children': [{
                        'id': 4,
                        'name': 'L4',
                        'children': [{
                            'id': 5,
                            'name': 'L5',
                            'children': []
                        }]
                    }]
                }]
            }]
        }]

        output_path = tmp_path / "deep.pptx"
        success, message = ppt_generator.generate(
            tree=deep_tree,
            stats=[],
            output_path=str(output_path)
        )

        assert success is True
        assert output_path.exists()

    def test_generate_with_wide_tree(self, ppt_generator, tmp_path):
        """测试宽树结构"""
        # 创建有多个子节点的树
        wide_tree = [{
            'id': 1,
            'name': 'Root',
            'children': [
                {'id': i, 'name': f'Dept{i}', 'children': []}
                for i in range(2, 12)  # 10 个子节点
            ]
        }]

        output_path = tmp_path / "wide.pptx"
        success, message = ppt_generator.generate(
            tree=wide_tree,
            stats=[],
            output_path=str(output_path)
        )

        assert success is True

    def test_generate_with_long_name(self, ppt_generator, tmp_path):
        """测试长名称处理"""
        tree = [{
            'id': 1,
            'name': '这是一个非常非常非常长的部门名称',
            'children': []
        }]

        output_path = tmp_path / "long_name.pptx"
        success, message = ppt_generator.generate(
            tree=tree,
            stats=[],
            output_path=str(output_path)
        )

        assert success is True
