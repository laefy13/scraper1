import json
import scrapy
from companyscraper.items import CompanyscraperItem
from urllib.parse import urlencode, urlparse, parse_qs


class CompanyrecognitionspiderSpider(scrapy.Spider):
    name = "companyrecognitionspider"
    allowed_domains = ["www.b.co.uk", "public.b.co.uk"]
    start_urls = ["https://www.b.co.uk"]

    def __init__(self):
        self.company_sizes = [
            "Small",
            "Mid-Sized",
            "Large",
            "Big",
        ]
        self.main_url = "https://public.b.co.uk/PublicSiteRankingAPI/Rankings"
        self.start_url = "https://www.b.co.uk/the-best-companies-to-work-lists"

    def parse(self, response):
        yield response.follow(
            self.start_url,
            callback=self.parseLinks,
        )

    def parseLinks(self, response):

        links = response.css(
            ".list-page-link-block.w-inline-block::attr(href)"
        ).getall()[5:]

        for link in links:
            full_url = response.urljoin(link)
            parsed_url = urlparse(full_url)
            query_params = parse_qs(parsed_url.query)
            form_data = {
                "CompanySize": query_params.get("CompanySize", ""),
                "sector": query_params.get("sector", ""),
                "region": query_params.get("region", ""),
                "limit": 50,
                "Offset": 0,
            }

            query_string = urlencode(form_data)
            request_url = f"{self.main_url}?{query_string}"

            yield scrapy.Request(
                url=request_url,
                callback=self.parseCompanies,
                meta={"form_data": form_data},
            )

    def parseCompanies(self, response):
        json_data = json.loads(response.text)
        form_data = response.meta["form_data"]

        if response.status == 405:
            self.logger.warning(f"Received 405 Method Not Allowed for {response.url}.")
            return

        if json_data["lstLeagueTableCompanies"]:
            for data in json_data["lstLeagueTableCompanies"]:
                yield scrapy.Request(
                    self.start_urls[0] + data["profileURL"],
                    callback=self.parseCompanyInformation,
                )

            form_data["Offset"] += 50

            query_string = urlencode(form_data)
            request_url = f"{self.main_url}?{query_string}"
            yield scrapy.Request(
                url=request_url,
                callback=self.parseCompanies,
                meta={"form_data": form_data},
            )

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
            .get(): stat_support.xpath("./preceding-sibling::*[1]")
            .xpath("string()")
            .get()
            for stat_support in response.css(".stat-support-text")[2:]
        }

        company_item["quote"] = {
            "text": response.xpath('//div[@data-external-id="quote"]')
            .xpath("string()")
            .get(),
            "position_and_name": response.xpath(
                '//div[@data-external-id="quote-attribute"]'
            )
            .xpath("string()")
            .get(),
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
