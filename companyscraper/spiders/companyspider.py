import scrapy

from companyscraper.items import CompanyscraperItem


class CompanyspiderSpider(scrapy.Spider):
    name = "companyspider"
    allowed_domains = ["www.b.co.uk"]
    start_urls = ["https://www.b.co.uk"]

    def __init__(self):
        self.urls = [
            "https://www.b.co.uk/accreditation/3-star",
            "https://www.b.co.uk/accreditation/2-star",
            "https://www.b.co.uk/accreditation/1-star",
            "https://www.b.co.uk/accreditation/ones-to-watch",
        ]

    def parse(self, response):
        for url in self.urls:
            yield response.follow(url, callback=self.parseCompanies)

    def parseCompanies(self, response):
        links_el = response.xpath('//a[contains(text(), "View Profile")]')

        for link_el in links_el:
            link = link_el.xpath("@href").get()
            yield response.follow(link, callback=self.parseCompanyInformation)
        next_page = response.xpath('//a[@aria-label="Next Page"]/@href').get()

        if next_page:
            yield response.follow(next_page, callback=self.parseCompanies)

    def parseCompanyInformation(self, response):
        company_item = CompanyscraperItem()
        company_item["name"] = (
            response.xpath('//h1[@data-external-id="name"]').xpath("string()").get()
        )

        company_item["about"] = (
            response.xpath('//div[@data-external-id="about"]').xpath("string()").get()
        )

        company_item["factors"] = [
            {
                "factor_name": container.css(".topfactorname::text").get(),
                "factor_stat_percentage": container.css(
                    ".topfactorstat h4::text"
                ).get(),
                "factor_stat_sub": container.css(".topfactorstat p::text").get(),
                "factor_description": container.css(".factor-description::text").get(),
            }
            for container in response.css(".topfactorcontainer")
        ]

        company_item["establishment_year"] = response.css(
            ".stat-support-text.established::text"
        ).get()

        company_item["quick_facts"] = {
            stat_support.css("::text")
            .get(): stat_support.xpath("./preceding-sibling::*[1]/text()")
            .get()
            for stat_support in response.css(".stat-support-text")[2:]
        }

        company_item["quote"] = {
            "text": response.xpath('//div[@data-external-id="quote"]').get(),
            "position_and_name": response.xpath(
                '//div[@data-external-id="quote-attribute"]'
            ).get(),
        }

        company_item["benefits"] = {
            benefit_container.css("h4 .benefittitle::text")
            .get(): benefit_container.css("p .benefitdescription::text")
            .get()
            for benefit_container in response.css(".benefitcontainer")
        }

        company_item["achievements"] = [
            {
                achievement_container.css(".league-table-block-title::text")
                .get(): achievement_container.css(".position.w-clearfix::text")
                .get(),
                "achievement_description": achievement_container.css(
                    ".league::text"
                ).get(),
            }
            for achievement_container in response.css(
                ".league-table-block:not(.w-condition-invisible)"
            )
        ]

        yield company_item
