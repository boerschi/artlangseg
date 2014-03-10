library(ggplot2)

# setwd("~/Desktop/artlangseg/writeup/plots/")
dat <- read.csv("scores.csv",sep="\t",header=T)

# ggplot(data=data,aes(x=struct,y=tf,colour=lang))+geom_line()+facet_grid(facets=dist~.)
# simple = lm(tf~nse,data=data)
# cor.test(data$tf,data$nse)

dat = dat[dat$dist != "zipf",]
dat$dist = factor(dat$dist)

pdf("roberts_second_try.pdf")
ggplot(dat) +
  geom_line(aes(x=tl, y=tf, linetype=lang)) +
  geom_point(aes(x=tl, y=nse, shape=lang)) +
  facet_grid(dist ~ .)
dev.off()

