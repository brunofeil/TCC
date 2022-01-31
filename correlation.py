# Pearson correlation
#Checking if there is continuous data that has a strong correlation with Person correlation
plt.figure(figsize=(18,16))
plt.title('Spearman correlation of continuous features', y=1.05, size=30)
sns.heatmap(df.corr(method='spearman'),linewidths=0.5,vmax=1.0, square=True, cmap=colormap, linecolor='white', annot=True)
