library(ggplot2)

# setwd("~/Desktop/artlangseg/writeup/plots/")
setwd("~/research/ArtificialLanguages/writeup/plots/")
dat <- read.csv("scores.csv",sep="\t",header=T)

# ggplot(data=data,aes(x=struct,y=tf,colour=lang))+geom_line()+facet_grid(facets=dist~.)
# simple = lm(tf~nse,data=data)
cor.test(subset(dat,dist=="bbr")$token.f.score,subset(dat,dist=="bbr")$nse)

dat = dat[dat$dist != "zipf",]
dat$dist = factor(dat$dist)

pdf("bens_version_2.pdf")
ggplot(dat) +
  geom_line(aes(x=token.length, y=token.f.score, linetype=language, colour=language),size=1.5) +
  geom_point(aes(x=token.length, y=token.f.score, shape=language, colour=language),size=4.0) +
  geom_point(aes(x=token.length, y=nse, colour=language, shape=language),size=3.0) +
  facet_grid(. ~ dist) +
  xlab("token length") +
  ylab("token f-score and NSE") +
  opts(legend.position="top") +
  scale_y_continuous(breaks=seq(0,1,0.1)) +
  theme_bw()
  dev.off()

