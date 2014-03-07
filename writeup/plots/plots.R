library(ggplot2)
# will need to adjust this to your directory structure
setwd("~/research/ArtificialLanguages/writeup/plots/")
data <- read.csv("scores.csv",sep="\t",header=T)


ggplot(data=data,aes(x=struct,y=tf,colour=lang))+geom_line()+facet_grid(facets=dist~.)

simple = lm(tf~nse,data=data)
cor.test(data$tf,data$nse)