尚硅谷大模型技术之机器学习

（作者：尚硅谷研究院）

版本：V2.0.3

1. 机器学习概述

*For more than 250 years, technological innovation has been the main driver of economic growth… The most important general-purpose technology of our era is artificial intelligence, particularly machine learning.*

*250 多年来，技术创新一直是经济增长的核心驱动力。而我们这个时代最重要的****通用技术（General-Purpose Technology, GPT）****，就是****人工智能****，尤其是****机器学习****。*

——Erik Brynjolfsson（数字经济学家：埃里克·布林约尔松，斯坦福大学）、Andrew McAfee（麻省理工学院），《哈佛商业评论》

**通用技术**的经济学定义

满足以下 3 个核心条件，才能被定义为通用技术：

* **广泛应用（Pervasiveness）：**可渗透到经济社会的各个行业
* **持续改进（Improvement）：**技术本身具备持续迭代、性能不断提升的能力
* **催生创新（Innovation Spawning）：**能带动上下游技术、产品、商业模式的创新

**典型案例：**蒸汽机、电力、人工智能均属于通用技术；iPhone 仅为终端产品，不满足通用技术定义。

* 1. 什么是机器学习

**机器学习**是一门让计算机从**数据中自动归纳规律**，并**利用规律**实现**预测**或**决策**的学科。其核心逻辑打破了传统编程 “硬编码规则” 的模式，转而依靠**数据驱动**。

机器学习最核心的三个问题：

* **学什么**：确定用何种数学函数 / 模型去拟合数据规律。

常见模型有：线性模型、多项式模型、决策树、神经网络（深度学习基础）等。

**核心任务是模型选择。**

* **怎么学**：确定评价标准（如损失函数），并通过算法寻找最优参数组合。

核心方法有：解析法（直接计算）、梯度下降法（迭代优化，最常用）等。

**核心任务是参数训练。**

* **学的好不好**：验证模型的预测 / 决策结果是否准确。

通过测试集数据检验模型泛化能力，避免 “过拟合” 或 “欠拟合”。

**核心任务是模型的评估。**

* 1. 机器学习发展历史

![](images/937868fd-a78c-47f8-9a7e-82ca6ababa77.x-emf)

* 1. 人工智能、机器学习、深度学习的关系

![](images/05fa4b89-65b5-4dd9-8b27-9404d6b71185.png)

* 1. 机器学习应用领域

现在机器学习已经可以应用在大量的领域中。

![文本  中度可信度描述已自动生成](images/4648c111-669b-4208-aac9-acd46653416f.png)

* 1. 机器学习分类
     + - 1. 有监督学习

基于**带标签（标准答案）的训练数据**，学习输入到输出的映射规律，用于预测和分类。

* + - * 1. 无监督学习

基于**无标签的训练数据**，挖掘数据本身的统计规律、潜在特征或聚类结构。

* + - * 1. 半监督学习

结合**少量带标签和大量无标签数据**，利用无标签数据提升模型泛化能力，降低标注成本。

* + - * 1. 强化学习

智能体通过与环境交互、试错，以奖励或惩罚为反馈，自主学习最优决策策略。

![](images/5241c9c3-e478-48a2-8893-abebf47fe288.x-emf)

* 1. 机器学习中的一些专业术语

![](images/1114d5eb-ddba-410b-be9d-947d8ac41c11.x-emf)

* **数据集（Data Set）：**多条记录的集合。
* 训练集（Training Set）：用于训练模型的数据。
* 验证集（Validation Set）：用于调节超参数的数据。
* 测试集（Test Set）：用于评估模型性能的数据。
* **样本（Sample）：**数据集中的一条记录是关于一个事件或对象的描述，称为一个样本。
* **特征（Feature）：**数据集中一列反映事件或对象在某方面的表现或性质的事项，称为特征或属性。
* **特征向量（Feature Vector）：**将样本的所有特征表示为向量的形式，输入到模型中。
* **标签（Label）：**监督学习中每个样本的结果信息，也称作目标值（target）。
* **模型（Model）：**一个机器学习算法与训练后的参数集合，用于进行预测或分类。
* **参数（Parameter）：**模型通过训练学习到的值，例如线性回归中的权重和偏置。
* **超参数（Hyper Parameter）：**由用户设置的参数，不能通过训练自动学习，例如学习率、正则化系数等。

1. 机器学习建模
   1. 监督学习一般建模流程

![](images/d1af5eb4-d7a6-4c77-9143-b1ca4e802bda.x-emf)

* 1. 数据收集

根据模型将来的一应用场景，收集相关行业的数据，用于训练和测试，确保数据能代表实际问题的不同方向。

![](images/6472f639-7674-4776-bee1-90ba480f78e2.png)

* 1. 数据清洗

在收集的数据中可能会有一些脏数据和不可用数据，需要提前剔除这些数据。

![](images/edf446f7-6596-40f1-816a-15dbbf179d01.png)

* 1. 特征工程

特征工程（Feature Engineering）是机器学习过程中非常重要的一步，指的是通过对**原始数据**的**处理、转换和构造**，生成**新的特征**或选择有**效的特征**，从而提高模型的性能。

简单来说，特征工程是将原始数据转换为可以更好地表示问题的特征形式，帮助模型更好地理解和学习数据中的规律。

优秀的特征工程可以显著提高模型的表现；反之，忽视特征工程可能导致模型性能欠佳甚至模型无法训练。

* + 1. 特征选择
       1. 特征选择介绍
          1. 什么是特征选择？

从原始特征中挑选出与目标变量（标签）关系最密切的特征，剔除冗余、无关或噪声特征。

* + - * 1. 为什么进行特征选择？

这样可以减少模型的复杂度、加速训练过程、并减少过拟合的风险。

特征选择不会创建新特征，也不会改变数据结构。

* + - * 1. 举例：

预测房价，原始特征有：房屋面积、朝向、房主手机号、门牌号、楼层、周边奶茶店数量。

特征选择后：删掉手机号、门牌号（无关噪声），保留面积 / 楼层 / 周边配套（有效特征）。

![](images/acf057fd-11e5-4c72-a924-9182c1a83f29.x-emf)

* + - 1. 特征选择代码演示
         1. 低方差过滤

import numpy as np
from sklearn.feature\_selection import VarianceThreshold

*# 1. 构造特征 1: 均值0 标准差1*a = np.random.randn(10000)
print(f'方差: ${np.var(a)}, 均值: ${np.mean(a)}')

*# 2. 构造特征 2: 均值5 标准差0.1*b = np.random.normal(loc=5, scale=0.1, size=10000)
print(f'方差: ${np.var(b)}, 均值: ${np.mean(b)}')

*# 3. 构造特征向量*X = np.vstack((a, b)).T
print(X)

*# 4. 方差过滤:删除方差低于0.2的特征*var\_thresh = VarianceThreshold(0.2)
X\_filtered = var\_thresh.fit\_transform(X)
print(X\_filtered)
print(X\_filtered.shape)
print(X.shape)

* + - * 1. 皮尔逊相关系数

*# 1. 读取数据*adv = pd.read\_csv("../data/advertising.csv")
print(adv.head())

*# 2. 数据清洗: 去掉id列*adv.drop(adv.columns[0], axis=1, inplace=True)
adv.dropna(inplace=True)

*# 3. 提取特征和标签*x = adv.drop("Sales", axis=1, inplace=False)
y = adv["Sales"]

*# 4. 计算皮尔逊相关系数*corr = x.corrwith(y, method="pearson")
print(corr)

![](images/ab9db527-bcd0-4231-939c-b582c396fc52.png)

*# 5. 相关系数矩阵*matrix = adv.corr(method="pearson")
print(matrix)

![](images/db53d466-5ba5-4312-a433-5a4211cd71c0.png)

*# 5.热力图*import matplotlib.pyplot as plt
import seaborn as sns
sns.heatmap(matrix, cmap="coolwarm", fmt=".2f", annot=True)
plt.show()

![](images/b07af550-4297-423e-8a27-fa94fd8b606d.png)

* + 1. 特征转换
       1. 特征转换介绍

特征转换是对数据做数学 / 统计处理，使其适配模型输入要求。

根据转换方式不同，一般把特征分为**数字型特征**和**类别型特征。**

![](images/43fb1462-4d66-48cc-bdd3-19ee210d70d0.x-emf)

![](images/4b2f9ffe-aece-4c02-b16d-fd026e7461dc.x-emf)

* + - 1. 特征转换代码演示
         1. 归一化

import numpy as np
from sklearn.preprocessing import MinMaxScaler

x = [[1, 2], [0.5, 6], [0, 10], [1, 18]]

*# 得到归一化的缩放器对象*scaler = MinMaxScaler(feature\_range=(0, 1))
x = scaler.fit\_transform(x)
print(x)

![](images/0ab9f73e-015f-40b5-96de-bb4635f3a646.png)

* + - * 1. 标准化

import numpy as np
from sklearn.preprocessing import StandardScaler

x = [[1, 2], [0.5, 6], [0, 10], [1, 18]]

scaler = StandardScaler()
x = scaler.fit\_transform(x)
print(x)

![](images/797f327a-b09e-445e-957c-5c0f8eeba5c6.png)

* + - * 1. 标签编码

from sklearn.preprocessing import LabelEncoder

data = ['本科','硕士','博士','本科']

encoder = LabelEncoder()

result = encoder.fit\_transform(data)

print(result)

![](images/a95301a4-a9ba-4a68-89a0-fa3a3f1085ae.png)

* + - * 1. 独热编码

from sklearn.preprocessing import OneHotEncoder
import numpy as np

X = np.array([['红'],
 ['蓝'],
 ['绿'],
 ['红']])

encoder = OneHotEncoder()
result = encoder.fit\_transform(X).toarray()

print(result)

![](images/8593dac1-df11-4d79-88ea-0b99515d8413.png)

* + 1. 特征构造

特征构造是基于现有的特征创造出新的、更有代表性的特征。通过**组合、转换、或者聚合**现有的特征，形成能够更好反映数据规律的特征。

![](images/cdd553bb-0f62-4ed0-98b1-b97d88ebfa1c.x-emf)

* + 1. 特征降维
       1. 特征降维介绍

当数据集的特征数量非常大时，特征降维可以帮助减少计算复杂度并避免过拟合。通过降维方法，可以在保持数据本质的情况下减少特征的数量。

![](images/bcbaef86-f723-4134-836a-1e214d4a7fdd.x-emf)

* + - 1. 特征降维代码演示
         1. PCA主成分分析

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

n = 1000
*# 1. 构造特征
# 1.1 生成主成分*pc1 = np.random.normal(0, 1, n)
pc2 = np.random.normal(0, 0.5, n)
*# 1.2 定义噪声*noise = np.random.normal(0, 0.1, n)

f1 = pc1 + pc2
f2 = pc1 - pc2
f3 = pc1 + noise

print(f1.shape)
print(f2.shape)
print(f3.shape)

x = np.vstack([f1, f2, f3]).T
print(x.shape)

*# 2. 主成分分析 浮点数: 表示保留的信息量 整数:保留的维度数*pca = PCA(n\_components=0.9)
x\_pac = pca.fit\_transform(x)
print(pca.explained\_variance\_ratio\_)
print(x\_pac.shape)

*# 3. 画图*fig = plt.figure(figsize=(12, 4))

*# 定义第一个子图*ax1 = fig.add\_subplot(121, projection='3d')
ax1.scatter(x[:, 0], x[:, 1], x[:, 2], c='g')
ax1.set\_title("Before PCA(3D)")
ax1.set\_xlabel("Feature1")
ax1.set\_ylabel("Feature2")
ax1.set\_zlabel("Feature3")

*# 定义第二个子图*ax2 = fig.add\_subplot(122)
ax2.scatter(x\_pac[:, 0], x\_pac[:, 1], c='g')
ax2.set\_title("After PCA(2D)")
ax2.set\_xlabel("PC1")
ax2.set\_ylabel("PC2")

plt.show()

![](images/c01dbf84-ca44-4aaf-aa29-ac6d3f53a254.png)

* 1. 算法（模型）选择和模型训练

后面专门讲到具体的模型时再细讲，这里先跳过。

* 1. 模型评估的通用方法
     1. 损失函数

**损失函数**是衡量模型预测好坏的标尺，也是指导模型进行优化的“指挥棒”。

简单来说，**损失函数**就是衡量我们模型预测结果好坏的一把尺子。就像打靶一样，子弹离靶心越远，损失就越大；子弹越靠近靶心，损失就越小。在机器学习中，“靶心”就是真实值，“子弹”就是模型的预测值。

**损失函数的核心作用**有两个：第一，评估模型的预测精度；第二，为模型的优化指明了方向。我们训练模型的过程，就是不断调整模型参数，努力让损失函数的值变得越来越小的过程。

![](images/a6ac833a-fb66-4076-9492-5a3438ec9bce.x-emf)

* + 1. 经验误差和泛化误差

给定一个训练数据集，数据个数为n：

根据选取的损失函数，就可以计算出模型*f(X)*在训练集上的平均误差，称为训练误差，也被称作 **经验误差**（empirical error） 或 **经验风险**（empirical risk）。

类似地，在测试数据集上平均误差，被称为测试误差或者 **泛化误差**（generalization error）。

一般情况下对模型评估的策略，就是考察经验误差；当经验风险最小时，就认为取到了最优的模型。这种策略被称为 **经验风险最小化**（empirical risk minimization，ERM）。

* + 1. 欠拟合与过拟合（修改）

拟合的过程，就像是我们根据现有的数据点，画一条最能代表这些数据趋势的曲线。这条曲线就是我们训练出来的模型。它的目标是尽可能地贴近数据，捕捉数据背后的规律。一个好的拟合模型，应该能够很好地解释已知数据，并对未知数据做出准确的预测。

![](images/8964eccc-4415-44c0-94cc-3ab3a50f07a5.x-emf)

使用多项式在上拟合：

* **泰勒展式：**

用多项式在某一点附近“逼近”一个复杂函数。

* **一维泰勒展式：**

![](images/5f56cec6-6a0d-45ed-91c4-ae1e62540dd1.png)

使用多项式在上拟合：

![](images/252a0052-9c8b-4a77-be3e-10589514cb0b.png)

*# 演示拟合: 恰好拟合 过拟合 欠拟合*import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear\_model import LinearRegression *# 线性回归模型*from sklearn.preprocessing import PolynomialFeatures *# 构建多项式特征*from sklearn.model\_selection import train\_test\_split *# 划分数据集: 训练集 测试集*from sklearn.metrics import mean\_squared\_error *# 均方误差损失函数(自己看)

# plt显示中文
#plt.rcParams["font.sans-serif"] = ["KaiTi"] # windows 系统*plt.rcParams["font.sans-serif"] = ["SongTi SC"] *# macos 系统
# 不适用unicode的 -号*plt.rcParams["axes.unicode\_minus"] = False

*# 1. 读取数据(生成数据: 特征和标签)*x = np.linspace(-np.pi, np.pi, 300).reshape(-1, 1)
y = np.sin(x) + np.random.uniform(-0.8, 0.8, 300).reshape(-1, 1)

*# 散点图*fig, axs = plt.subplots(1, 3, figsize=(15, 4))
axs[0].scatter(x, y)
axs[1].scatter(x, y)
axs[2].scatter(x, y)
*# 2. 数据清洗(略)

# 3. 划分数据集: 训练集 测试集*train\_x, test\_x, train\_y, test\_y = train\_test\_split(x, y, test\_size=0.2, random\_state=42)
print(train\_x.shape, test\_x.shape)
*# 4. 定义模式: 线性回归模型*model = LinearRegression()

*# 欠拟合
# 5. 训练模型*model.fit(train\_x, train\_y)
print(model.coef\_, model.intercept\_) *# 参数和截距
# 6. 模型评估 (看损失值)*train\_loss = mean\_squared\_error(train\_y, model.predict(train\_x))
test\_loss = mean\_squared\_error(test\_y, model.predict(test\_x))
print(f"欠拟合: 训练误差: {train\_loss}, 测试误差: {test\_loss}")
*# 7. 绘制曲线*axs[0].plot(x, model.predict(x), c='r')
axs[0].text(-3, 1, f"测试集均方误差：{test\_loss:.4f}")
axs[0].text(-3, 1.3, f"训练集均方误差：{train\_loss:.4f}")
print(model.score(test\_x, test\_y))

*# 恰好拟合
# 特征工程*poly5 = PolynomialFeatures(degree=5) *# 构建多项式特征*train\_x2 = poly5.fit\_transform(train\_x) *# 训练集都是fit\_transform*test\_x2 = poly5.transform(test\_x) *# 测试集都是transform*print(train\_x2.shape, test\_x2.shape)
*# 5. 训练模型*model.fit(train\_x2, train\_y)
print(model.coef\_, model.intercept\_) *# 参数和截距
# 6. 模型评估 (看损失值)*train\_loss = mean\_squared\_error(train\_y, model.predict(train\_x2))
test\_loss = mean\_squared\_error(test\_y, model.predict(test\_x2))
print(f"恰好拟合: 训练误差: {train\_loss}, 测试误差: {test\_loss}")
*# 7. 绘制曲线*axs[1].plot(x, model.predict(poly5.transform(x)), c='r')
axs[1].text(-3, 1, f"测试集均方误差：{test\_loss:.4f}")
axs[1].text(-3, 1.3, f"训练集均方误差：{train\_loss:.4f}")
print(model.score(test\_x2, test\_y))

*# 过拟合
# 特征工程*poly20 = PolynomialFeatures(degree=20) *# 构建多项式特征*train\_x3 = poly20.fit\_transform(train\_x) *# 训练集都是fit\_transform*test\_x3 = poly20.transform(test\_x) *# 测试集都是transform*print(train\_x3.shape, test\_x3.shape)
*# 5. 训练模型*model.fit(train\_x3, train\_y)
print(model.coef\_, model.intercept\_) *# 参数和截距
# 6. 模型评估 (看损失值)*train\_loss = mean\_squared\_error(train\_y, model.predict(train\_x3))
test\_loss = mean\_squared\_error(test\_y, model.predict(test\_x3))
print(f"过拟合: 训练误差: {train\_loss}, 测试误差: {test\_loss}")
*# 7. 绘制曲线*axs[2].plot(x, model.predict(poly20.transform(x)), c='r')
axs[2].text(-3, 1, f"测试集均方误差：{test\_loss:.4f}")
axs[2].text(-3, 1.3, f"训练集均方误差：{train\_loss:.4f}")
print(model.score(test\_x3, test\_y))
plt.show()

![](images/27fd96b2-72cb-4eec-bb4b-63c528d185f5.png)

当多项式次数较低时，模型过于简单，拟合效果较差。

当多项式次数增加后，模型复杂度适中，拟合效果较好，训练误差和测试误差均较低。

当多项式次数继续增加，模型变得过于复杂，过度学习了噪声，导致训练误差较低而测试误差较高。

* + 1. 正则化

正则化（Regularization）是一种在训练机器学习模型时，在损失函数中添加额外项，来惩罚过大的参数，进而限制模型复杂度、避免过拟合，提高模型泛化能力的技术。

如在平方损失函数中加入正则化项：

这里用 表示模型参数。

* 原损失函数 的目的：更好的拟合数据集。
* 正则化项的目的：减小参数的大小，从而降低模型的复杂度。

这里的 是 **正则化系数**，用来表示惩罚项的权重。正则化系数不属于模型的参数，无法通过训练学习得到，需要在模型训练开始之前手动设置，这种参数被称为“**超参数**”。

两者相互平衡，在模型的拟合能力（偏差）和复杂度之间找到最佳折中。

常见的正则化技术有L1正则化和L2正则化。

* + - * 1. L1正则化（Lasso回归）

L1正则化在损失函数中加入参数的绝对值之和：

L1正则化通过惩罚模型参数的绝对值，使得部分权重趋近0甚至变为0。这会导致特征选择，即模型会自动“丢弃”一些不重要的特征。L1正则化有助于创建稀疏模型（即许多参数为0）。在解决回归问题时，使用L1正则化也被称为“Lasso回归”。

超参数控制着正则化的强度。较大的 值意味着强烈的正则化，会使模型更简单，可能导致欠拟合。而较小的 值则会使模型更复杂，可能导致过拟合。

* + - * 1. L2正则化（Ridge回归，岭回归）

L2正则化在损失函数中加入参数的平方之和：

L2正则化通过惩罚模型参数的平方，使得所有参数都变得更小，但不会将参数强行压缩为0。它会使得模型尽量平滑，从而防止过拟合。

在解决回归问题时，使用L2正则化也被称为“岭回归”。

* + - * 1. ElasticNet正则化（弹性网络回归）

ElasticNet正则化结合了L1和L2正则化，通过调整两个正则化项的比例来取得平衡，从而同时具备稀疏性和稳定性的优点。

，决定L1和L2的权重。

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear\_model import LinearRegression, Lasso, Ridge *# 线性回归模型 和 拉索回归 和 岭回归*from sklearn.preprocessing import PolynomialFeatures *# 构建多项式特征*from sklearn.model\_selection import train\_test\_split *# 划分数据集: 训练集 测试集*from sklearn.metrics import mean\_squared\_error *# 均方误差损失函数(自己看)

# plt显示中文
# plt.rcParams["font.sans-serif"] = ["KaiTi"] # windows 系统*plt.rcParams["font.sans-serif"] = ["SongTi SC"] *# macos 系统
# 不使用unicode的 -号*plt.rcParams["axes.unicode\_minus"] = False

*# 1. 读取数据(生成数据: 特征和标签)*x = np.linspace(-np.pi, np.pi, 300).reshape(-1, 1)
y = np.sin(x) + np.random.uniform(-0.5, 0.5, 300).reshape(-1, 1)

*# 散点图*fig, axs = plt.subplots(2, 3, figsize=(15, 8))
axs[0, 0].scatter(x, y)
axs[0, 1].scatter(x, y)
axs[0, 2].scatter(x, y)
*# 2. 数据清洗(略)

# 3. 划分数据集: 训练集 测试集*train\_x, test\_x, train\_y, test\_y = train\_test\_split(x, y, test\_size=0.2, random\_state=42)
print(train\_x.shape, test\_x.shape)
*# 4. 定义模式: 线性回归模型*model = LinearRegression()

*# 过拟合
# 特征工程*poly20 = PolynomialFeatures(degree=20) *# 构建多项式特征*train\_x = poly20.fit\_transform(train\_x) *# 训练集都是fit\_transform*test\_x = poly20.transform(test\_x) *# 测试集都是transform*print(train\_x.shape, test\_x.shape)

*# 5. 训练模型*model.fit(train\_x, train\_y)
print(model.coef\_, model.intercept\_) *# 参数和截距
# 6. 模型评估 (看损失值)*test\_loss = mean\_squared\_error(test\_y, model.predict(test\_x))
print(f"过拟合: 测试误差: {test\_loss}")
*# 7. 绘制曲线*axs[0, 0].plot(x, model.predict(poly20.transform(x)), c='r')
axs[0, 0].text(-3, 1, f"测试集均方误差：{test\_loss:.4f}")
axs[1, 0].bar(np.arange(len(model.coef\_.reshape(-1))), model.coef\_.reshape(-1))

*# Lasso 回归 L1*model = Lasso(alpha=0.009) *# alpha 正则话强度*model.fit(train\_x, train\_y)
test\_loss = mean\_squared\_error(test\_y, model.predict(test\_x))
print(model.coef\_, model.intercept\_)
print(f"Lasso: 测试误差: {test\_loss}")

axs[0, 1].plot(x, model.predict(poly20.transform(x)), c='r')
axs[0, 1].text(-3, 1, f"测试集均方误差：{test\_loss:.4f}")
axs[1, 1].bar(np.arange(len(model.coef\_.reshape(-1))), model.coef\_.reshape(-1))

*# Ridge 回归 L2*model = Ridge(alpha=0.009) *# alpha 正则话强度*model.fit(train\_x, train\_y)
test\_loss = mean\_squared\_error(test\_y, model.predict(test\_x))
print(model.coef\_, model.intercept\_)
print(f"Ridge: 测试误差: {test\_loss}")

axs[0, 2].plot(x, model.predict(poly20.transform(x)), c='r')
axs[0, 2].text(-3, 1, f"测试集均方误差：{test\_loss:.4f}")
axs[1, 2].bar(np.arange(len(model.coef\_.reshape(-1))), model.coef\_.reshape(-1))
plt.show()

![](images/91ab5a43-c17a-44bb-8ad1-f12b008c4975.png)

* + 1. 交叉验证

交叉验证（Cross-Validation）是一种评估模型泛化能力的方法，通过将数据集划分为多个子集，反复进行训练和验证，以减少因单次数据划分带来的随机性误差。通过交叉验证能更可靠地估计模型在未知数据上的表现，亦能避免因单次数据划分不合理导致的模型过拟合或欠拟合。

* + - * 1. 简单交叉验证（Hold-Out Validation）

将数据划分为训练集和验证集（如70%训练，30%验证）。结果受单次划分影响较大，可能高估或低估模型性能。

* + - * 1. k折交叉验证（k-Fold Cross-Validation）

将数据均匀分为k个子集（称为“折”），每次用k−1折训练，剩余1折验证，重复k次后取平均性能。充分利用数据，结果更稳定。

![图形用户界面, 应用程序  描述已自动生成](images/ccde70c0-ef16-44b3-b558-ff240d3e272f.png)

* + - * 1. 留一交叉验证（Leave-One-Out，LOO）

每次仅留一个样本作为验证集，其余全部用于训练，重复直到所有样本都被验证一次。适用于小数据集，计算成本极高。

* + 1. 模型评估指标

对学习的泛化性能进行评估，不仅需要有效可行的实验估计方法，还需要有衡量模型泛化能力的评价指标，也叫做性能度量（performance measure）。

* + - 1. 回归模型评估指标

模型的评价指标用于衡量模型在训练集或测试集上的性能，评估结果反映了模型预测的准确性和泛化能力。

对于回归问题，最常用的性能度量是“均方误差” (Mean Squared Error，MSE)。

* + - * 1. 平均绝对误差（MAE）
* MAE对异常值不敏感，解释直观。适用于数据包含异常值的场景。
  + - * 1. 均方误差（MSE）
* MSE会放大较大误差，对异常值敏感。适用于需要惩罚大误差的场景。
  + - * 1. 均方根误差（RMSE）
* 与MSE类似，但量纲与目标变量一致。适用于需要直观误差量纲的场景。如果一味地试图降低RMSE，可能会导致模型对异常值也拟合度很高，容易过拟合。
  + - * 1. R²（决定系数）
* 衡量模型对目标变量的解释能力，越接近1越好，对异常值敏感。
* 模型完美拟合，预测值和真实值完全相等
* 模型预测不如直接用均值，解释不了数据波动
* 模型预测比均值差，说明模型很差

model.score(test\_x, test\_y) # 这个分数就是计算的决定系数

* + - 1. 分类模型评估指标

对于分类问题，最常用的指标就是“准确率”（Accuracy），它定义为分类器对测试集正确分类的样本数与总样本数之比。此外还有一系列常用的评价指标。

* + - * 1. 混淆矩阵

混淆矩阵（Confusion Matrix）是用于评估分类模型性能的工具，展示了模型预测结果与实际标签的对比情况。

对于二分类问题，混淆矩阵是一个2×2矩阵：

![表格  描述已自动生成](images/ce0c94bc-94ff-498e-a66f-732bfa558a5a.png)

例如，有10个样本。6个是猫，4个是狗。假设以猫为正例，模型预测对了5个猫，2个狗。

![表格, 日历  描述已自动生成](images/bebd4371-70d4-4fb1-9b71-67267c6b2383.png)

import sklearn.metrics as metrics
import pandas as pd

y\_true = ["猫", "猫", "猫", "猫", "猫", "猫", "狗", "狗", "狗", "狗"] *# 真实值*y\_pred = ["猫", "猫", "狗", "猫", "猫", "猫", "猫", "猫", "狗", "狗"]

labels = ["猫", "狗"]

matrix = metrics.confusion\_matrix(y\_true, y\_pred, labels=labels)

df = pd.DataFrame(matrix, index=labels, columns=labels)
print(df)

![](images/b1b90a9c-b46c-4ab2-addc-969c5955a69a.png)

* + - * 1. 准确率（Accuracy）

正确预测的比例。

![表格  描述已自动生成](images/17494d1b-5795-4843-9e1c-f7b68d6a4dcb.png)

上述案例中，。

print(metrics.accuracy\_score(y\_true, y\_pred))

* + - * 1. 精确率（Precision）

精确率：预测为正例的样本中实际为正例的比例，也叫查准率。

![表格  描述已自动生成](images/a5321ab5-c1ea-4e6e-aa34-f7b06d15b827.png)

上述案例中，。

*# 精确率 (查准率)*print(metrics.precision\_score(y\_true, y\_pred, pos\_label="猫"))

* + - * 1. 召回率（Recall）

召回率：实际为正类的样本中预测为正类的比例，也叫查全率。

![表格  描述已自动生成](images/d7470b3a-ff22-45da-a444-af0a986cf296.png)

上述案例中，。

*# 召回率(查全率)*print(metrics.recall\_score(y\_true, y\_pred, pos\_label="猫"))

* + - * 1. F1分数（F1 Score）

F1分数：**精确率**和**召回率**的调和平均。

上述案例中，。

print(metrics.f1\_score(y\_true, y\_pred, pos\_label="猫"))

* + - * 1. 评估报告

可通过sklearn.metrics.classification\_report生成分类任务的评估报告，包括**精确率**、**召回率**、**F1分数**等。

*# 评估报告*print(metrics.classification\_report(y\_true, y\_pred, labels=labels))

![](images/4243f37c-8268-4581-956b-e45e2fd60155.png)

* + - * 1. ROC曲线
* **真正例率（TPR）：**实际为正例，被预测为正例的比例，即召回率。
* **假正例率（FPR）：**实际为负例，被预测为正例的比例。
* **阈值（Threshold）：**根据阈值将概率转换为类别标签。

ROC曲线（Receiver Operating Characteristic Curve，受试者工作特征）是评估二分类模型性能的工具，以假正例率（FPR）为横轴，以真正例率（TPR）为纵轴，展示不同阈值下模型的表现。绘制ROC曲线时，从高到低调整阈值，计算每个阈值的TPR和FPR并绘制所有阈值的点，形成ROC曲线。

![](images/7a061e60-1778-46c1-a8a2-9ba269d720e6.png)

假设一个二分类模型的真实标签和模型输出概率如下：

调整阈值，计算TPR和FPR：

根据坐标点绘制ROC曲线：

![](images/8e33a087-32fb-4414-b235-efede0f576b7.png)

当点足够多的时候，就平滑了。

* + - * 1. AUC值

AUC值代表ROC曲线下的**面积**，用于量化模型性能。AUC值越大，模型区分正负类的能力越强，模型性能越好。AUC值=0.5表示模型接近随机猜测，AUC值=1代表完美模型。

from sklearn.datasets import make\_classification *# 自动生成分类的数据集*from sklearn.model\_selection import train\_test\_split *# 数据集的划分*from sklearn.linear\_model import LogisticRegression *# 逻辑回归模型*from sklearn.metrics import classification\_report *# 评估报告

# 1. 生成数据*x, y = make\_classification(n\_samples=1000, n\_features=20, n\_classes=2, random\_state=42)

*# 2. 划分数据集*train\_x, test\_x, train\_y, test\_y = train\_test\_split(x, y, test\_size=0.2, random\_state=42)
*# 3. 定义模型: 逻辑回归模型*model = LogisticRegression()

*# 4. 训练模型*model.fit(train\_x, train\_y)

*# 5. 使用测试集预测结果*pred\_y = model.predict(test\_x)

*# 6.计算auc的值*from sklearn.metrics import roc\_auc\_score

*# auc的值: 参数1: 真实标签, 参数2: 预测的概率*print(roc\_auc\_score(test\_y, model.predict\_proba(test\_x)[:, 1]))

1. 线性回归模型
   1. 线性回归模型介绍
      1. 什么是线性回归

**线性回归（Linear Regression）**是一种用于建模两个或多个变量之间**线性关系**的统计方法。它通过拟合**一条直线（或超平面）**来描述自变量（输入特征）与因变量（输出目标）之间的关联，并可用于预测或分析变量间的影响关系。

假设因变量与自变量之间的关系可以用如下线性方程表示：

* ：截距，模型在自变量全为0时的基准值
* ：自变量的系数，表示每个自变量对因变量的影响程度

通过估计这些系数，使模型预测值尽可能接近真实值。

* + - * 1. 一元线性回归

仅有一个自变量：。

![](images/28f134da-773c-4f60-a1e8-75840659f12f.png)

* + - * 1. 多元线性回归

包含多个自变量：。

![](images/ce679797-d6cd-4681-8005-a089c6769211.png)

* + 1. 线性回归应用场景
* **GDP预测：**用历史数据（如投资、消费、出口）建立回归模型，预测GDP增长趋势。
* **广告效果评估：**量化不同渠道广告投入对销售额的影响，优化预算分配。
* **药物剂量研究：**分析药物剂量与患者生理指标（如血压、血糖）之间的关系。
* **产品质量控制：**通过生产参数（温度、压力、原料配比）预测产品性能（如强度、耐久）。
* **政策效果评估：**分析最低工资政策对就业率的影响，或环保法规对污染排放的抑制作用。
* **气候变化建模：**用工业排放量、森林覆盖率等变量预测全球气温变化趋势。

总结：只要关系是线性的，都可以使用线性回归模型。

* + 1. 线性回归简单案例

例如，某中学教师想研究学生每周学习时间（小时）与数学考试成绩（0-100分）之间的关系，并预测学生成绩。

from sklearn.linear\_model import LinearRegression

*# 1. 准备数据*X = [[5], [8], [10], [12], [15], [3], [7], [9], [14], [6]]

y = [55, 65, 70, 75, 85, 50, 60, 72, 80, 58]

*# 2. 创建模型*model = LinearRegression()

*# 3. 训练模型*model.fit(X, y)

*# 4. 查看模型参数*print(model.coef\_)
print(model.intercept\_)

*# 5. 预测*print(model.predict([[30]]))

*# 6. 绘图*import matplotlib.pyplot as plt
import numpy as np

x\_line = np.arange(0, 20, 0.1).reshape(-1, 1)
y\_line = model.predict(x\_line)

plt.plot(x\_line, y\_line)

plt.scatter(X, y, c='b')

plt.scatter(11, model.predict([[11]]), c='r')

plt.show()

![](images/6851ad05-30b2-46b2-9c49-24b777a969f1.png)

* 1. 损失函数

模型的**预测值**与**真实值**之间存在**误差**。

![](images/063f7781-ed7f-4148-b387-d373357b9e77.png)

损失函数用于衡量模型预测值与真实值之间的误差，并通过**最小化损失函数**来优化模型参数。当损失函数最小时，得到的自变量系数就是最优解。

* + 1. 均方误差损失函数

线性回归模型默认采用的是**均方误差损失函数（MSE）**

* ：样本个数。
* ：第i个样本的真实值。
* ：第i个样本的预测值。
  + 1. 为什么选择均方误差损失函数

![](images/d68d5bb7-1c13-43f5-8024-2c95e818b177.png)

* + - 1. 优点
         1. 均方误差是凸函数，存在全局的唯一最小值，平方项又使损失函数处处可导，便于求解最优参数。
         2. 最小二乘法（最小化MSE）的解析解可通过矩阵运算直接求出（如）
         3. 若误差服从正态分布，则均方误差对应极大似然估计，是最优的损失函数。

![](images/f4dee540-c756-471e-8b52-1ff44f3d6d9f.x-emf)

* + - 1. 缺点

均方误差对大误差比较敏感，因为平方项会放大较大的误差（如误差2→4，误差10→100）。

* 1. 求解算法
     1. 解析法
        1. 一元线性回归解析解

![](images/c6218893-0ed1-4880-9736-d8f57c6a3833.x-emf)

以前述学生每周学习时间（小时）与数学考试成绩（0-100分）之间的关系为例：

# 自变量，每周学习时长

X = [[5], [8], [10], [12], [15], [3], [7], [9], [14], [6]]

# 因变量，数学考试成绩

y = [55, 65, 70, 75, 85, 50, 60, 72, 80, 58]

解得

* + - 1. 正规方程法（解析法）

![](images/1ccd82a3-fb75-43c9-9214-75da0bcc6510.x-emf)

* + 1. 梯度下降法（一阶迭代优化算法）
       1. 介绍

**梯度下降法**（gradient descent）是一种常用的一阶优化方法，是求解无约束优化问题最简单、最经典的方法之一。梯度下降法是**迭代算法**，基本思路就是先选取一个适当的初始值，然后沿着梯度方向或者负梯度方向，不停地更新参数，最终取到极小值。

![](images/0cd2dba0-5cdc-42c5-9383-ccc84142dc9b.png)

* **梯度方向：**函数变化增长最快的方向（变量沿此方向变化时函数增长最快）
* **负梯度方向：**函数变化减少最快的方向（变量沿此方向变化时函数减少最快）

因为损失函数是系数的函数，那么如果系数沿着损失函数的负梯度方向变化，此时损失函数减少最快，能够以最快速度下降到极小值。

这里的代表第k次迭代时的参数值，而 是参数取值为时损失函数 的梯度； 是每次迭代的“步长”，被称为“**学习率**”。学习率也是一个常见的超参数，需要手动设置，选择不当会导致收敛失败。

* + - 1. 特点

梯度下降不一定能够找到全局的最优解，有可能是一个局部最优解。

* **优点：**适用性广；计算简单；
* **缺点：**收敛速度慢；可能陷入局部最优。
  + - 1. 分类
         1. 批量梯度下降（Batch Gradient Descent，BGD）

每次迭代使用全部训练数据计算梯度。

* **优点：**稳定收敛。
* **缺点：**计算开销大。
  + - * 1. 随机梯度下降（Stochastic Gradient Descent，SGD）

每次迭代随机选取一个样本计算梯度。

* **优点：**速度快，适合大规模数据。
* **缺点：**梯度更新方向不稳定，优化过程震荡较大，可能难以收敛。
  + - * 1. 小批量梯度下降（Mini-batch Gradient Descent，MBGD）

每次迭代使用一小批样本（如32、64个）计算梯度。

平衡了BGD的稳定性和SGD的速度，是最常用的方法。

* + - * 1. 计算步骤

**初始化参数：**随机选择初始参数

**计算梯度：**在当前参数下，计算**损失函数的梯度**

**更新参数：**沿负梯度方向调整参数

**重复迭代：**直到满足停止条件（如梯度接近零、达到最大迭代次数等）

* + - 1. 手动梯度下降法简单案例演示

以前述学生每周学习时间（小时）与数学考试成绩（0-100分）之间的关系为例。

自变量（学习时长）。

因变量（数学考试成绩） 。

求 使得损失函数最小，为此需要求出损失函数相对的梯度。

添加一列1，转换为。则损失函数

。

求得损失函数的梯度

使用梯度下降法求解。

* 初始值取
* 学习率取0.01

![](images/301f690d-e447-419b-bb5c-80bfa588bc33.png)

import numpy as np
x = np.array([[5], [8], [10], [12], [15], [3], [7], [9], [14], [6]]) *# 自变量，每周学习时长*x = np.hstack((np.ones((10, 1)), x))

y = np.array([[55], [65], [70], [75], [85], [50], [60], [72], [80], [58]]) *# 因变量，数学考试成绩*n = x.shape[0]
*# 定义损失函数和梯度函数
# beta是一个向量 (beta0, beta2,...., beta10)*def lose(beta):
 return np.sum((x @ beta - y) \*\* 2) /n

def grad(beta):
 return (x.T @ (x @ beta - y)) / n \* 2

*# 初始化参数和学习率*beta = np.array([ [1], [1 ] ])
alpha = 0.01
iter = 10000

beta0= []
beta1= []

for i in range(iter):
 beta0.append(beta[0][0])
 beta1.append(beta[1][0])
 *# 计算梯度* beta = beta - alpha \* grad(beta)

 print(f"第{i+ 1}次迭代: \n {beta}")

import matplotlib.pyplot as plt
plt.plot(beta0, beta1)
plt.show()

![](images/27077343-d98e-426b-ad5f-45eca34b64cb.png)

* + - 1. 学习率的选择
* **学习率过大：**可能导致跳过最优解，甚至发散。
* **学习率过小：**收敛速度慢，易陷入局部极小。
* **自适应学习率：**高级优化器（如Adam、Adagrad）动态调整学习率以提升性能。
  + - 1. 梯度下降法常见问题
         1. 收敛速度慢 - 特征缩放

通常需要提前对特征进行缩放（如标准化或归一化），以加快收敛速度。

* + - * 1. 局部极小值、鞍点问题

可能陷入局部极小值（非全局最优解），或遇到鞍点（梯度为零但非极值点）。

**解决方案：**使用动量（Momentum）、自适应优化器（如Adam）或二阶方法（如牛顿法）。

* + 1. 牛顿法和拟牛顿法（二阶迭代优化算法）

牛顿法也是求解无约束最优化问题的常用方法，核心思想是利用目标函数的**二阶导数信息**，通过迭代逐渐逼近极值点。

这里的表示损失函数黑塞矩阵的逆在点的取值。

* **优点：**收敛速度快；精度高；
* **缺点：**计算复杂；可能发散。

由于牛顿法中需要计算黑塞矩阵的逆，这一步比较复杂；所以可以考虑用一个n阶正定矩阵来近似代替它，这种方法称为“拟牛顿法”。

牛顿法和拟牛顿法一般用于解决中小规模的凸优化问题。

* 1. 案例:广告效果预测
     1. 数据集说明

Advertising数据集：<https://www.kaggle.com/datasets/tawfikelmetwally/advertising-dataset>。

* **ID：**序号。
* **TV：**电视广告投放金额，单位千元。
* **Radio：**广播广告投放金额，单位千元。
* **Newspaper：**报纸广告投放金额，单位千元。
* **Sales：**销售额，单位百万元。
  + 1. 具体实现代码

import pandas as pd *# 读取数据*from sklearn.model\_selection import train\_test\_split *# 划分数据集*from sklearn.preprocessing import StandardScaler *# 标准化缩放器*from sklearn.linear\_model import LinearRegression, SGDRegressor *# 线性回归模型*from sklearn.metrics import mean\_squared\_error *# 均方误差损失

# 1. 读取数据*dataset = pd.read\_csv("../data/advertising.csv")
*# 2. 数据清洗*dataset.drop(dataset.columns[0], axis=1, inplace=True) *# 去掉id列*dataset.dropna(inplace=True)
*# 4. 划分数据集*x = dataset.drop("Sales", axis=1)
y = dataset["Sales"]
train\_x, test\_x, train\_y, test\_y = train\_test\_split(x, y, test\_size=0.2, random\_state=42)
*# 5. 特征工程*scaler = StandardScaler()
train\_x = scaler.fit\_transform(train\_x) *# 训练集标准化*test\_x = scaler.transform(test\_x) *# 测试集标准化

# 6. 选择模型*model\_lr = LinearRegression()
model\_sgd = SGDRegressor()
*# 7. 模型训练(分别训练)*model\_lr.fit(train\_x, train\_y)
model\_sgd.fit(train\_x, train\_y)

*# 8. 查看参数*print(f'线性回归模型参数: \n {model\_lr.coef\_} \n {model\_lr.intercept\_}')
print(f'随机梯度下降模型参数: \n {model\_sgd.coef\_} \n {model\_sgd.intercept\_}')
*# 8. 测试评估*pred\_lr = model\_lr.predict(test\_x)
pred\_sgd = model\_sgd.predict(test\_x)

*# 查看损失*print(f'线性回归模型损失: \n {mean\_squared\_error(test\_y, pred\_lr)}')
print(f'随机梯度下降模型损失: \n {mean\_squared\_error(test\_y, pred\_sgd)}')

*# 查看决定系数*print(f'线性回归模型决定系数: \n {model\_lr.score(test\_x, test\_y)}')
print(f'随机梯度下降模型决定系数: \n {model\_sgd.score(test\_x, test\_y)}')

1. 逻辑回归模型
   1. 逻辑回归模型介绍
      1. 什么是逻辑回归

逻辑回归（Logistic Regression）是一种用于解决**分类问题**的统计方法，尤其适用于二分类问题。尽管名称中有“回归”，但它主要用于分类任务。

逻辑回归通过将线性回归的输出映射到[0,1]区间，来表示某个类别的概率。

常用的映射函数是sigmoid函数：，其导数。

![](images/14dede2a-1b7b-4903-9702-f766c7dcc958.png)

逻辑回归结果可表示为：

其中为线性回归输出结果，表示输出为1类的概率。

根据**逻辑回归结果**和**阈值**来确认最终预测结果，若逻辑回归结果大于阈值则输出为1类，反之输出为0类。

* + 1. 逻辑回归应用场景
* **信用评分：**预测客户是否会违约（违约/不违约）。
* **欺诈检测：**预测某笔交易是否是欺诈行为。
* **垃圾邮件检测：**预测一封邮件是否是垃圾邮件（垃圾邮件/非垃圾邮件）。
* **广告点击预测：**预测用户是否会点击某个广告（点击/不点击）。
* **图像分类：**将图像分类为不同的类别（如猫、狗、鸟等）。
* **情感分析：**将文本分类为正面、负面或中性情感。
* **产品质量分类：**预测产品是否合格。
* **医学诊断：**预测患者是否患有某种疾病（患病/未患病）。
* **蛋白质功能预测：**基于蛋白质序列和结构特征预测其功能类别。
  1. 二分类任务

二分类任务指的时候，预测结果只有两种情况。

* + 1. 损失函数

逻辑回归针对二分类问题的损失函数通常使用**对数损失**（Log Loss），也称为**二元交叉熵损失**（Binary Cross-Entropy Loss），用于衡量模型输出的概率分布与真实标签之间的差距。逻辑回归的损失函数来源于**最大似然估计**（MLE）。

![](images/aed59248-ec5a-4f33-bf75-a82ccf3cbddb.x-emf)

* + 1. API介绍

# solver: 优化算法

#   lbfgs: 拟牛顿法（默认），仅支持L2正则化

#   newton-cg: 牛顿法，仅支持L2正则化

#   liblinear: 坐标下降法，适用于小数据集，支持L1和L2正则化

#   sag: 随机平均梯度下降，适用于大规模数据集，仅支持L2正则化

#   saga: 改进的随机梯度下降，适用于大规模数据，支持L1、L2和ElasticNet正则化

# penalty: 正则化类型，可选l1、l2和elasticnet

# C: 正则化强度，C越小，正则化强度越大

# class\_weight: 类别权重，balanced表示自动平衡类别权重，让模型在训练时更关注少数类，从而减少类别不平衡带来的偏差

model = sklearn.linear\_model.LogisticRegression(solver="lbfgs", penalty="l2", C=1, class\_weight="balanced")

* + 1. 案例：心脏病预测
       1. 数据集说明

Heart Disease数据集<https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset>。

* **年龄：**连续值
* **性别：**0-女，1-男
* **胸痛类型：**0-典型心绞痛，1-非典型心绞痛，2-非心绞痛，3-无症状
* **静息血压：**连续值，单位mmHg
* **胆固醇：**连续值，单位mg/dl
* **空腹血糖：**1-大于120mg/dl，0-小于等于120mg/dl
* **静息心电图结果：**0-正常，1-ST-T异常，2-可能左心室肥大
* **最大心率：**连续值
* **运动性心绞痛：**1-有，0-无
* **运动后的ST下降：**连续值
* **峰值ST段的斜率：**0-向上，1-水平，2-向下
* **主血管数量：**0到3
* **地中海贫血：**一种先天性贫血，0-正常，1-固定缺陷，2-可逆缺陷
* **是否患有心脏病：**标签，0-否，1-是
  + - 1. 特征工程
         1. 特征转换

数据集中包含多种类型的特征：

* **类别型特征**（需要特殊处理）

**胸痛类型：**4种分类（名义变量）

**静息心电图结果：**3种分类（名义变量）

**峰值ST段的斜率：**3种分类（有序变量）

**地中海贫血：**4种分类（名义变量）

* **数值型特征：**年龄、静息血压、胆固醇、最大心率、运动后的ST下降、主血管数量
* **二元特征（保持原样）：**性别、空腹血糖、运动性心绞痛

对于数值型特征，可以直接进行标准化。

对于类别型特征，直接使用整数编码的类别特征会被算法视为有序数值，导致错误的距离计算（例如：会认为 胸痛类型=1 和 胸痛类型=2 之间的差异比 胸痛类型=1和 胸痛类型=3之间差异更小，而实际上它们都是类别）。使用 **独热编码**（One-Hot Encoding）可将类别特征转换为二元向量，消除虚假的顺序关系。

![墙上的钟表  中度可信度描述已自动生成](images/4c4ae23d-0b9f-4bf3-bd80-7e29f466f873.png)

* + - * 1. 避免多重共线性

drop="first"是独热编码中的一个参数，它的核心目的是避免多重共线性（Multicollinearity）。

多重共线性是指特征之间存在高度线性相关关系的现象。例如特征胸痛类型包含4个类别（0、1、2、3），若直接进行独热编码会生成4个新列（胸痛类型\_0、胸痛类型\_1、胸痛类型\_2、胸痛类型\_3），此时这4列满足。

这种完全线性相关关系会导致特征矩阵的列之间存在完美共线性。

当特征矩阵存在多重共线性时，模型参数估计会变得不稳定（矩阵不可逆或接近奇异），导致系数估计值方差增大、模型可解释性下降、过拟合等问题。

在独热编码时设置drop="first"，会删除每个类别特征的第1列，从而打破完全共线性。比如特征胸痛类型会生成3列（胸痛类型\_1、胸痛类型\_2、胸痛类型\_3），此时

![图形用户界面, 应用程序, 表格  中度可信度描述已自动生成](images/7707f2b4-2481-476c-be09-9e7c373c6fd1.png)

* + - 1. 具体实现代码

import pandas as pd
from sklearn.compose import ColumnTransformer

from sklearn.model\_selection import train\_test\_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder *# 标准化 独热编码 缩放器*from sklearn.linear\_model import LogisticRegression

*# 1. 读取数据*dataset = pd.read\_csv("../data/heart\_disease.csv")

*# 2. 数据清洗*dataset.dropna(inplace=True)
print(dataset.shape)

*# 3. 划分标签和特征*x = dataset.drop("是否患有心脏病", axis=1) *# 特征*y = dataset["是否患有心脏病"] *# 标签
# 4. 划分训练集和测试集*train\_x, test\_x, train\_y, test\_y = train\_test\_split(x, y, test\_size=0.3, random\_state=42)
*# 5. 特征工程(数值做标准化 类别:独热编码)*numerical\_features = ["年龄", "静息血压", "胆固醇", "最大心率", "运动后的ST下降", "主血管数量"]
*# 类别型特征*categorical\_features = ["胸痛类型", "静息心电图结果", "峰值ST段的斜率", "地中海贫血"]
*# 二元特征*binary\_features = ["性别", "空腹血糖", "运动性心绞痛"]

*# 列转换器*column\_transformer = ColumnTransformer([
 ("num", StandardScaler(), numerical\_features),
 ("cate", OneHotEncoder(drop="first"), categorical\_features),
 ("bin", "passthrough", binary\_features)
])
train\_x = column\_transformer.fit\_transform(train\_x)
test\_x = column\_transformer.transform(test\_x)
print(train\_x.shape)
print(test\_x.shape)

*# 6. 定义模型: 逻辑回归模型*model = LogisticRegression(
 C=1.0,
 solver="lbfgs",
 max\_iter=10000,
)
*# 7. 训练模型*model.fit(train\_x, train\_y)

*# 8.评估模型*print(model.score(test\_x, test\_y)) *# 准确率*

* 1. 多分类任务

逻辑回归通常用于二分类问题，但可以通过一对多（One-vs-Rest，OvR）或Softmax回归（Multinomial Logistic Regression，多项逻辑回归）来扩展到多分类任务。

* + 1. 实现方式1：OvR（One-vs-Rest：一对多）
       1. 实现原理

若有C个类别，则训练C个二分类逻辑回归分类器。每个分类器将一个类别作为正例、所有其他类别作为反例。

预测时，计算C个分类器的输出概率，选取概率最高的类别。

对于类别：

* + - 1. 优缺点

**优点：**简单易于实现，适用于类别数量较少的情况。

**缺点：**每个类别训练1个分类器，当类别数量较多时，训练时间较长。

* + - 1. API

from sklearn.linear\_model import LogisticRegression

# 这个参数从1.5开始标记位过时, 1.8开始被移除, 不建议使用

model = LogisticRegression(multi\_class="ovr")

# 或

from sklearn.multiclass import OneVsRestClassifier

model = OneVsRestClassifier(LogisticRegression())

* + 1. 实现方式2：softmax回归（多项逻辑回归）
       1. 实现原理

逻辑回归模型中的线性拟合部分会为每个分类输出一个**分数**，然后把每个分数交给softmax函数，每个分类都会得到一个概率分布，所有分类的概率分布的和是1。然后从所有分类的概率分布中，选择一个最大概率对应的分类作为预测结果。

只需训练1个逻辑回归模型。

预测时用1个模型计算所有类别的概率，选择最大值。

若有C个类别，模型将输出C个分数。

每个分类会有一套单独的参数。

对于类别，。

其中为示性函数，当时值为1，反之值为0。

* + - 1. 优缺点

**优点：**只训练1个模型，计算高效，分类一致性更好。（所有分类概率和为1）。

**缺点：**计算Softmax需要对所有类别求指数，计算量较高。

* + - 1. API

from sklearn.linear\_model import LogisticRegression

model = LogisticRegression(multi\_class="multinomial")

# 对于多分类问题，LogisticRegression会自动使用multinomial，因此multi\_class参数可省略

model = LogisticRegression()

* + 1. 多分类案例：手写数字识别（使用softmax回归）
       1. 数据集说明

Digit Recognizer数据集：<https://www.kaggle.com/competitions/digit-recognizer>。

文件train.csv中包含手绘数字（从0到9）的灰度图像，每张图像为28×28像素，共784像素。每个像素有一个0到255的值表示该像素的亮度。

文件第1列为标签，之后784列分别为784个像素的亮度值。

第个像素表示图像第行第列的像素。

![](images/8020b7b4-768f-481c-bc3f-c328c67fdf3e.png)

* + - 1. 具体实现代码

import pandas as pd
from sklearn.linear\_model import LogisticRegression
from sklearn.model\_selection import train\_test\_split
from sklearn.preprocessing import MinMaxScaler

import matplotlib.pyplot as plt
import joblib

*# 1. 读取数据172.17.0.132*dataset = pd.read\_csv("../data/train.csv")
*# 显示图片
# plt.imshow(dataset.iloc[0, 1:].values.reshape(28, -1), cmap="Grays\_r")
# plt.show()

# 3. 划分标签和特征
# x = dataset.drop("label", axis=1)*x = dataset.iloc[:, 1:]
y = dataset.iloc[:, 0]
print(x.shape, y.shape)

*# 3. 划分训练集和测试集*train\_x, test\_x, train\_y, test\_y = train\_test\_split(x, y, test\_size=0.2, random\_state=42)

*# 4. 特征工程: 归一化*scaler = MinMaxScaler()
train\_x = scaler.fit\_transform(train\_x)
test\_x = scaler.transform(test\_x)

*# 5. 定义模型: 逻辑回归模型
#model = LogisticRegression(max\_iter=10000)
# 6. 训练模型
#model.fit(train\_x, train\_y)

# 保存模型
#joblib.dump(model, "digital.model")

# 加载模型*model = joblib.load("digital.model")

*# 7. 评估模型(分数: 准确率)*print(model.score(test\_x, test\_y))

*# 8. 预测*pred\_y = model.predict(test\_x[20].reshape(1, -1)) print(model.predict\_proba(test\_x[20].reshape(1, -1)))
print(pred\_y)

plt.imshow(test\_x[20].reshape(28, -1), cmap="Grays\_r")
plt.show()

1. 感知机
   1. 感知机介绍

感知机（Perceptron）是二分类模型，接收多个信号，输出一个信号。感知机的信号只有0、1两种取值。下图是一个接收两个输入信号的感知机的例子：

![](images/3ded2507-0465-44d3-b776-079bfff4dcb2.png)

是输入信号，是输出信号，是权重，○称为神经元或节点。输入信号被送往神经元时，会分别乘以固定的权重。神经元会计算传送过来的信号的总和，只有当这个总和超过某个界限值时才会输出1，也称之为神经元被激活。这里将界限值称之为阈值。

感知机的多个输入信号都有各自的权重，这些权重发挥着控制各个信号的重要性的作用，权重越大，对应信号的重要性越高。

* 1. 感知机实现简单逻辑门
     1. 门电路
        1. 与门

尝试使用感知机解决简单的问题，如实现逻辑电路中的与门（AND gate）。与门是具有两个输入和一个输出的门电路，仅在两个输入均为1时输出1，其他时候输出0。这种输入信号和输出信号对应表称为真值表。

![表格  中度可信度描述已自动生成](images/8e60b8e6-c69f-4073-b1ea-1085b082d808.png)

使用感知机表示与门需要确定能满足上述真值表的的值，满足条件的参数有无数个，如。

* + - 1. 与非门

再来考虑下与非门（NAND gate），与非门颠倒了与门的输出，仅当同时为1时输出0，其他时候输出1。

![表格  中度可信度描述已自动生成](images/481cd726-1da0-432e-808d-8624699b7bb9.png)

要表示与非门，满足条件的参数也有无数个，如。实际上，只要把实现与门的参数值的符号取反即可。

* + - 1. 或门

再来看一下或门（OR gate）。或门只要有一个输入信号为1，输出就为1。

![表格  描述已自动生成](images/1cd4511b-04e7-48ab-a04d-dbc71b8bb216.png)

。

* + 1. 具体代码实现
       1. 简单实现

*# 简单实现*class Perceptron:
 def \_\_init\_\_(self, w1, w2, theta):
 self.w1 = w1
 self.w2 = w2
 self.theta = theta

 def predict(self, x1, x2):
 y = self.w1 \* x1 + self.w2 \* x2
 if y <= self.theta:
 return 0
 else:
 return 1

if \_\_name\_\_ == '\_\_main\_\_':
 and\_gate = Perceptron(0.5, 0.5, 0.7)
 print(and\_gate.predict(0, 0))
 print(and\_gate.predict(0, 1))
 print(and\_gate.predict(1, 0))
 print(and\_gate.predict(1, 1))

* + - 1. 导入权重和偏置

考虑到以后的事情，我们将其修改为另外一种实现形式。将换为，表示感知机行为的式子变为如下形式：

为偏置，为权重。下面我们使用Numpy按上述形式分别实现与门、与非门和或门。

import numpy as np

# 导入权重和偏置
class Perceptron:
 def \_\_init\_\_(self, w, b):
 self.w = w
 self.b = b

 def predict(self, x):
 y = self.w @ x + self.b
 if y <= 0:
 return 0
 else:
 return 1

if \_\_name\_\_ == '\_\_main\_\_':

 x1 = np.array([0, 0])
 x2 = np.array([0, 1])
 x3 = np.array([1, 0])
 x4 = np.array([1, 1])

 print("与门真值表")
 and\_gate = Perceptron(w=np.array([0.5, 0.5]), b=-0.7)
 print(and\_gate.predict(x1))
 print(and\_gate.predict(x2))
 print(and\_gate.predict(x3))
 print(and\_gate.predict(x4))

 print("或门真值表")
 or\_gate = Perceptron(w=np.array([0.5, 0.5]), b=0)
 print(or\_gate.predict(x1))
 print(or\_gate.predict(x2))
 print(or\_gate.predict(x3))
 print(or\_gate.predict(x4))

 print("与非门")
 nand\_gate = Perceptron(w=np.array([-0.5, -0.5]), b=0.7)
 print(nand\_gate.predict(x1))
 print(nand\_gate.predict(x2))
 print(nand\_gate.predict(x3))
 print(nand\_gate.predict(x4))

* 1. 多层感知机
     1. 单层感知机的局限性

现在来考虑一下异或门（XOR gate）。异或门仅当或中的一方为1时才会输出1。

![表格  描述已自动生成](images/a2ed8853-64bb-4ecc-b575-fc101fce5573.png)

之前的感知机是无法实现这个异或门的，具体原因让我们来分析一下。

感知机表示或门的式子如下：

上式表示感知机会生成由直线划分的两个空间，其中一个空间输出1，另一个空间输出0，如图：

![图表  描述已自动生成](images/88045c85-5dd4-44f9-94f9-8c3549fcc265.png)

如果要实现异或门，是无法使用一条直线将0和1分开的：

![绿色的球  中度可信度描述已自动生成](images/6af86a6e-85f3-47f8-95d8-a21c5c5ad90c.png)

但如果将直线这个限制条件去掉就可以了：

![图片包含 图表  描述已自动生成](images/62260a53-5c49-4c06-8a5c-ffeb16a0a74c.png)

感知机的局限性就在于它只能表示由一条直线划分的空间，而上图中的曲线无法用感知机表示。由曲线划分的空间称为非线性空间，由直线划分的空间称为线性空间。

* + 1. 多层感知机实现或非门

我们先来考虑一下如何使用与门、与非门和或门来组合出异或门。

与门、与非门、或门用下图的符号表示：

![图表, 箱线图  描述已自动生成](images/6611f892-d28e-4e01-af54-ad9e1b8260b8.png)

将其组合构成异或门：

![图示  描述已自动生成](images/ed8d3e1a-2bdd-44df-8c32-f38ee6b55d1c.png)

![表格  描述已自动生成](images/557a6186-9987-4776-94d2-3b2bab6f27a3.png)

使用之前实现的与门、与非门和或门代码来实现异或门：

print("异或门")
def xor(x):
 s1 = nand\_gate.predict(x)
 s2 = or\_gate.predict(x)
 return and\_gate.predict(np.array([s1, s2]))