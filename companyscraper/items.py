# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CompanyscraperItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    about = scrapy.Field()
    factors = scrapy.Field()
    establishment_year = scrapy.Field()
    quick_facts = scrapy.Field()
    quote = scrapy.Field()
    benefits = scrapy.Field()
    achievements = scrapy.Field()
    pass
