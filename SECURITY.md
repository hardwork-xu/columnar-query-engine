# Security / 安全说明

Experimental local software, no network listener or credentials. Process only trusted, reasonably sized arrays/NPZ archives. Loading uses allow_pickle=False, but compressed data can exhaust memory; this package is not a sandbox. Python callers can access private internals despite read-only API views. No claims of adversarial file isolation or crash-safe persistence.

本项目无网络监听或凭据。仅处理可信且大小合理的数组/NPZ；禁用pickle不等于防御压缩包资源耗尽，只读视图也不是Python恶意调用者隔离机制。不提供事务级崩溃保护。

Supported security-fix line: 0.1.x. Use GitHub private vulnerability reporting if available; do not post secrets or private archives in public issues. If that channel is unavailable, share only a non-sensitive description until a private channel is established. 未配置的报告通道不应被假定可用。
