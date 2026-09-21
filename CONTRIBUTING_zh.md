# 贡献指南

[English](CONTRIBUTING.md)。创建虚拟环境并按README安装，执行make test/lint/build。公共接口及docs/en、docs/zh须同步。修改剪枝边界时增加独立标量参考和极值相等测试；摘要无法判断时必须扫描，不能丢行。

实验变更先于测量记录，保留全部退化试次，用python -m segmentlens report生成README表格，使用新结果文件名并保留历史记录。使用Conventional Commits。复制第三方代码必须记录来源并保留许可，不宣称成熟机制为首次发明；私人文件与凭据留在仓库外。
