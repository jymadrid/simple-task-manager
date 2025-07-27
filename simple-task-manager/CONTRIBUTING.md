# 🤝 贡献指南

感谢你对简单任务管理器项目的兴趣！我们欢迎各种形式的贡献。

## 🎯 贡献方式

### 1. 报告Bug 🐛

如果你发现了bug，请：

1. 检查 [Issues](../../issues) 确保bug未被报告
2. 创建详细的bug报告，包括：
   - 清晰的描述
   - 重现步骤
   - 期望行为
   - 实际行为
   - 系统环境信息

### 2. 功能建议 💡

对于新功能建议：

1. 检查现有的 [Issues](../../issues) 和 [Discussions](../../discussions)
2. 创建功能请求，说明：
   - 功能的详细描述
   - 使用场景
   - 预期的用户体验

### 3. 代码贡献 🔧

#### 开发环境设置

1. **Fork 项目**
   ```bash
   # 在GitHub上点击 Fork 按钮
   ```

2. **克隆你的Fork**
   ```bash
   git clone https://github.com/your-username/simple-task-manager.git
   cd simple-task-manager
   ```

3. **设置上游仓库**
   ```bash
   git remote add upstream https://github.com/original-owner/simple-task-manager.git
   ```

4. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### 代码规范

- 使用有意义的变量和函数名
- 添加适当的注释
- 遵循Python PEP 8规范
- 保持代码简洁易读

#### 提交规范

使用清晰的提交信息：

```bash
git commit -m "add: 添加任务优先级功能"
git commit -m "fix: 修复任务删除时的ID重排问题"
git commit -m "docs: 更新README中的使用说明"
```

#### 提交Pull Request

1. **更新你的分支**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **推送到你的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **创建Pull Request**
   - 提供清晰的PR标题和描述
   - 引用相关的Issue
   - 包含测试说明

## 📝 文档贡献

文档改进包括：

- README更新
- 代码注释改进
- 新功能文档
- 使用示例

## 🧪 测试

在提交PR前，请确保：

- [ ] 代码能正常运行
- [ ] 没有破坏现有功能
- [ ] 新功能按预期工作

## 🎨 设计原则

我们坚持以下设计原则：

1. **简单易用**: 保持界面和操作简洁
2. **功能完整**: 确保核心功能稳定可靠
3. **易于扩展**: 代码结构清晰，便于添加新功能
4. **学习友好**: 代码适合初学者理解和学习

## 📋 优先级任务

目前我们特别需要帮助的领域：

- [ ] 添加单元测试
- [ ] 性能优化
- [ ] 国际化支持
- [ ] Web界面开发
- [ ] 移动端适配

## 🎉 贡献者认可

所有贡献者都会被添加到项目的贡献者列表中。我们认可各种形式的贡献：

- 代码贡献
- 文档改进
- Bug报告
- 功能建议
- 设计改进
- 社区支持

## 📞 获取帮助

如果你需要帮助：

1. 查看现有的 [Issues](../../issues)
2. 参与 [Discussions](../../discussions)
3. 联系维护者

## 🔄 开发流程

1. **提交Issue** → 讨论功能/bug
2. **创建分支** → 开始开发
3. **编写代码** → 实现功能
4. **测试验证** → 确保质量
5. **提交PR** → 代码审查
6. **合并代码** → 功能发布

---

再次感谢你的贡献！让我们一起让这个项目变得更好！ 🚀
