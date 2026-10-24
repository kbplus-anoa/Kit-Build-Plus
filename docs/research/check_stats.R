# -*- coding: utf-8 -*-
suppressMessages({library(lme4); library(lmerTest); library(rstatix); library(pROC); library(psych)})
set.seed(20261025)

n <- 80; k_txt <- 2
mk <- function(n, group, r=0.5){
  subj <- rep(1:n, each=k_txt)
  txt  <- rep(c("T1","T2"), times=n)
  ord  <- rep(rep(c("AB","BA"), each=1), times=n/2)
  ord  <- rep(sample(c("AB","BA"), n, TRUE), each=k_txt)
  pre  <- rnorm(n*k_txt, 0.45, 0.15)
  post <- pre + ifelse(group=="exp", 0.18, 0.08) + rnorm(n*k_txt, 0, 0.08)
  post <- pmin(post, 0.98)
  data.frame(subj=factor(subj), group=factor(group), txt=factor(txt),
             ord=factor(ord), pre=pre, post=post)
}
d <- rbind(mk(n/2,"exp"), mk(n/2,"ctl"))
# normalized change
d <- transform(d, nc = ifelse(post>pre, (post-pre)/(1-pre),
                       ifelse(post<pre, (post-pre)/(pre-0), 0)))

cat("== 1. 前测同质性 (Mann-Whitney) ==\n")
print(wilcox_test(pre ~ group, data=d))
cat("\n== 2. 主模型 LMM: post ~ group*pre + txt + ord + (1|subj) ==\n")
m <- lmer(post ~ group*pre + txt + ord + (1|subj), data=d)
print(summary(m)$coefficients)

cat("\n== 3. 增益组间比较 (nc) ==\n")
print(wilcox_test(nc ~ group, data=d))
cat("效应量 r = Z/sqrt(N):\n")
w <- wilcox.test(nc ~ group, data=d, exact=FALSE)
cat(sprintf("  Z=%.3f  r=%.3f\n", qnorm(w$p.value/2), abs(qnorm(w$p.value/2))/sqrt(nrow(d))))

cat("\n== 4. 天花板检查 mean+SD vs max ==\n")
cat(sprintf("  post: mean=%.3f SD=%.3f mean+SD=%.3f max=%.3f  -> %s\n",
  mean(d$post), sd(d$post), mean(d$post)+sd(d$post), max(d$post),
  ifelse(mean(d$post)+sd(d$post) > max(d$post), "天花板征兆", "未见")))

cat("\n== 5. Review/New 四指标（同卷三时点）==\n")
set.seed(1)
d$delay <- pmin(d$post + rnorm(nrow(d), -0.05, 0.06), 1)
calc <- function(x, thr=0.5){
  pre_ok <- x$pre>=thr; post_ok <- x$post>=thr; del_ok <- x$delay>=thr
  data.frame(Review = mean(pre_ok & post_ok),
             New    = mean(!pre_ok & post_ok),
             ReviewOnDelay = mean(pre_ok & post_ok & del_ok),
             NewOnDelay    = mean(!pre_ok & post_ok & del_ok))
}
print(round(calc(d), 3))
cat(sprintf("  Normalized Review = %.3f\n", mean(d$post[d$pre>=0.5]>=0.5)/mean(d$pre>=0.5)))
cat(sprintf("  Normalized New    = %.3f\n", mean(d$post[d$pre<0.5]>=0.5)/mean(d$pre<0.5)))

cat("\n== 6. Cronbach alpha（TAM 7 题六点）==\n")
tam <- data.frame(
  PEOU1=sample(1:6,40,TRUE), PEOU2=sample(1:6,40,TRUE), PEOU3=sample(1:6,40,TRUE),
  PU1=sample(1:6,40,TRUE),   PU2=sample(1:6,40,TRUE),   PU3=sample(1:6,40,TRUE),
  BI1=sample(1:6,40,TRUE))
print(round(psych::alpha(tam)$total, 3))

cat("\n== 7. 抽崩检测器 ROC/AUC ==\n")
lab <- sample(c(0,1), 60, TRUE, prob=c(.7,.3))
sig <- ifelse(lab==1, rnorm(60, 2.2, 1), rnorm(60, 0.9, 1))
rocobj <- roc(lab, sig, quiet=TRUE)
cat(sprintf("  AUC = %.3f\n", auc(rocobj)))

cat("\n== 8. Dunn（多组，备用）==\n")
d3 <- data.frame(nc=rnorm(60), g=rep(c("A","B","C"), each=20))
print(rstatix::dunn_test(nc ~ g, data=d3, p.adjust.method="holm"))
