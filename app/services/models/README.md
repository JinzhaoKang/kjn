# 📚 模型管理说明文档

## 🤖 模型分类总览

### 1. **预训练模型（直接使用）** 
> **无需训练，自动下载，开箱即用**

| 模型名称 | 来源 | 大小 | 用途 | 是否必需 | GPU需求 |
|---------|------|------|------|----------|---------|
| SentenceTransformer | HuggingFace | ~90MB | 文本聚类 | ✅ 必需 | ❌ CPU |
| Chinese BERT | 哈工大 | ~400MB | 特征提取 | ⚠️ 可选 | ✅ GPU |
| Chinese Sentiment | UER | ~400MB | 情感分析 | ⚠️ 可选 | ✅ GPU |
| Jieba | PyPI | ~5MB | 中文分词 | ✅ 必需 | ❌ CPU |

### 2. **自定义模型（需要训练）**
> **需要用业务数据训练，专门针对反馈分析场景**

| 模型名称 | 算法 | 大小 | 用途 | 训练数据需求 |
|---------|------|------|------|-------------|
| Priority Classifier | RandomForest | ~10MB | 优先级分类 | 标注了优先级的反馈数据 |
| Category Classifier | MultinomialNB | ~5MB | 类别分类 | 标注了类别的反馈数据 |
| TF-IDF Vectorizer | TF-IDF | ~50MB | 特征提取 | 大量反馈文本 |
| Keyword Extractor | TF-IDF | ~20MB | 关键词提取 | 业务相关文本 |

## 🚀 模型处理策略

### **预训练模型处理**
```python
# 首次运行时自动下载
from transformers import AutoModel
model = AutoModel.from_pretrained("hfl/chinese-bert-wwm-ext")  # 自动下载

# 后续运行使用缓存
model = AutoModel.from_pretrained("hfl/chinese-bert-wwm-ext")  # 从缓存加载
```

### **自定义模型处理**
```python
# 1. 首次部署：训练模型
training_data = {
    "texts": ["反馈文本1", "反馈文本2", ...],
    "labels": ["high", "medium", ...]
}
result = await model_manager.train_model("priority_classifier", training_data)

# 2. 后续运行：加载已训练模型
model = await model_manager.load_model("priority_classifier")
```

## 💾 部署策略

### **开发环境**
```bash
# 1. 安装依赖
pip install transformers sentence-transformers torch scikit-learn

# 2. 初始化模型管理器
python -c "
from backend.app.services.models.model_manager import model_manager
import asyncio
asyncio.run(model_manager.initialize_all_models())
"
```

### **生产环境**
```bash
# 1. 预下载所有模型（可选）
python scripts/download_models.py

# 2. 使用已有的业务数据训练自定义模型
python scripts/train_custom_models.py --data-path /path/to/training_data.json

# 3. 启动服务
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## 🔧 模型管理API

### **模型状态查询**
```python
# 获取所有模型信息
info = model_manager.get_model_info()

# 检查特定模型
model = await model_manager.get_model("sentence_transformer")
```

### **模型训练**
```python
# 训练优先级分类器
training_data = load_training_data()
result = await model_manager.train_custom_model("priority_classifier", training_data)

if result.success:
    print(f"训练成功，准确率: {result.accuracy:.3f}")
```

### **模型更新**
```python
# 更新预训练模型
await model_manager.update_model("chinese_bert")

# 重新训练自定义模型
await model_manager.update_model("priority_classifier")
```

## 📊 存储结构

```
models/
├── pretrained/                    # 预训练模型缓存
│   ├── transformers/             # HuggingFace模型
│   └── sentence_transformers/    # SentenceTransformer模型
├── custom/                       # 自定义模型
│   ├── priority_classifier.joblib
│   ├── category_classifier.joblib
│   └── tfidf_vectorizer.joblib
└── logs/                         # 训练日志
    └── training_history.json
```

## ⚡ 性能优化

### **内存管理**
- 按需加载模型，避免一次性加载所有模型
- GPU模型优先级：BERT > Sentiment > Others
- 自动清理未使用的模型

### **加载优化**
- 异步加载，避免阻塞主线程
- 模型缓存，避免重复加载
- 失败降级，GPU模型失败时使用CPU替代方案

## 🔄 模型生命周期

### **1. 初始化阶段**
- ✅ 检查磁盘空间
- ✅ 下载必需的预训练模型
- ⚠️ 检查自定义模型是否存在
- ❌ 如果缺少自定义模型，使用默认规则

### **2. 运行阶段**
- 🔄 定期检查模型版本更新
- 📊 监控模型性能指标
- 🎯 根据新数据重训练模型

### **3. 维护阶段**
- 🧹 清理旧版本模型文件
- 📈 分析模型性能趋势
- 🔧 调整模型参数

## ❓ 常见问题

### **Q: 是否需要自己训练BERT模型？**
A: ❌ 不需要。使用预训练的中文BERT模型即可，如 `hfl/chinese-bert-wwm-ext`

### **Q: 自定义模型必须要训练吗？**
A: ✅ 是的。优先级分类器等必须用业务数据训练才有效果

### **Q: 如果没有训练数据怎么办？**
A: 🔄 系统提供fallback机制：
- 优先级分类 → 基于关键词规则
- 类别分类 → 基于业务关键词库
- 情感分析 → 基于情感词典

### **Q: 模型多久需要更新？**
A: 📅 建议策略：
- 预训练模型：季度检查更新
- 自定义模型：月度重训练（如果有新数据）
- 紧急情况：发现性能下降时立即重训练 