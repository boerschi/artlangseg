library(ggplot2)

# setwd("~/Desktop/artlangseg/writeup/plots/")
setwd("~/research/ArtificialLanguages/writeup/plots/")
dat <- read.csv("scores.csv",sep="\t",header=T)

# ggplot(data=data,aes(x=struct,y=tf,colour=lang))+geom_line()+facet_grid(facets=dist~.)
# simple = lm(tf~nse,data=data)
# cor.test(data$tf,data$nse)

dat = dat[dat$dist != "zipf",]
dat$dist = factor(dat$dist)

pdf("bens_version.pdf")
ggplot(dat) +
  geom_line(aes(x=token.length, y=token.f.score, linetype=language, colour=language),size=1.5) +
  geom_point(aes(x=token.length, y=token.f.score, colour=language),size=3.0,alpha=I(0.5)) +
  geom_point(aes(x=token.length, y=nse, shape=language, colour=language),size=3.5,alpha=I(0.8)) +
  facet_grid(dist ~ .) +
  xlab("token length") +
  ylab("token f-score and NSE") +
  opts(legend.position="top") +
  scale_y_continuous(breaks=seq(0,1,0.1))
  dev.off()

