import scrapy
import sys
import re
from bs4 import BeautifulSoup as bs
from scrapy.linkextractor import LinkExtractor
from scrapy.spiders import Rule, CrawlSpider
from items import DatabloggerScraperItem
from scrapy.http import HtmlResponse

class DiputadosSpider(scrapy.Spider):
    name = "diputados"

    # This spider has one rule: extract all (unique and canonicalized) links, follow them and parse them using the parse_items method
    rules = [
        Rule(
            LinkExtractor(
                canonicalize=True,
                unique=True
            ),
            follow=True,
            callback="parse_items"
        )
    ]

    allowed_domains = ['sitl.diputados.gob.mx']

    def start_requests(self):
        urls = [
            'http://sitl.diputados.gob.mx/LXI_leg/listado_diputados_gpnp.php?tipot=TOTAL',
            #'http://sitl.diputados.gob.mx/LXI_leg/curricula.php?dipt=179',
            #'http://sitl.diputados.gob.mx/LXI_leg/curricula.php?dipt=212',
            #'http://sitl.diputados.gob.mx/LXI_leg/curricula.php?dipt=794',
            #'http://sitl.diputados.gob.mx/LXI_leg/curricula.php?dipt=933',
            #'http://sitl.diputados.gob.mx/LXI_leg/curricula.php?dipt=193',
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    general_info = {'additional_info': [], 'basic_info': {}}

    def parse(self, response):
        #print 'table'
        items = []
        data = []
        for table in response.css('table'):
            
            for tds in table.css('td'):
                
                name = tds.css('a.linkVerde').extract()
                state = tds.css('td.textoNegro').extract()

                if len(name) > 0:
                    data.append(name[0])
                elif len(state) > 0 and len(data) > 0:
                    data.append(state[0])

                if len(data) >= 3:
                    soup = bs(data[0])

                    for i in soup.find_all('a'):
                        data[0] = i.text



                    link = None
                    for i in soup.find_all('a'):
                        link = i.get('href')
                        #data[0] = i.text
                    
                    yield scrapy.Request('http://sitl.diputados.gob.mx/LXI_leg/' + str(link), callback=self.parse_dir_contents)
                    
                    soup = bs(data[1])
                    for i in soup.find_all('td'):
                        data[1] = i.text

                    soup = bs(data[2])
                    for i in soup.find_all('td'):
                        data[2] = i.text

                    # The list of items that are found on the particular page
                    
                    # Only extract canonicalized and unique links (with respect to the current page)
                    res = HtmlResponse(url='http://sitl.diputados.gob.mx/LXI_leg/' + link)
                    links = LinkExtractor(canonicalize=True, unique=True).extract_links(res)
                    # Now go through all the found links
                    for link in links:
                        # Check whether the domain of the URL of the link is allowed; so whether it is in one of the allowed domains
                        is_allowed = False
                        for allowed_domain in self.allowed_domains:
                            if allowed_domain in link.url:
                                is_allowed = True
                        # If it is allowed, create a new item and add it to the list of found items
                        if is_allowed:
                            item = DatabloggerScraperItem()
                            item['url_from'] = response.url
                            item['url_to'] = link.url
                            #print 'response'
                            #print response.url
                            #print link.url
                            items.append(item)

                    
                    # Return all the found items
                    self.general_info['basic_info']['name'] = data[0]
                    self.general_info['basic_info']['state'] = data[1]
                    
                    '''
                    yield {
                        'name': data[0],
                        'link': link,
                        'state': data[1],
                        'district': data[2],
                    }
                    '''
                    data = []
                    



                
                #print name
        return

    def parse_dir_contents(self, response):
        print 'response'
        x = 0
        

        for table in response.css('table'):
            if x == 0:
                for tds in table.css('td'):
                    text = tds.css('td[width="530"]')
                    text = text.css('span.Estilo67').extract()
                    if len(text) > 0:

                        soup = bs(text[0])

                        title = None
                        for s in soup.find_all('span'):
                            title = s.text
                            self.general_info['basic_info']['name'] = title.strip()
            elif x == 1:
                for tds in table.css('td'):
                    text = tds.css('td.Estilo51').extract()

                    if len(text) > 0:
                        #print text[0]
                        soup = bs(text[0])

                        title = None
                        for s in soup.find_all('a'):
                            title = s.text

                        link = None
                        for s in soup.find_all('a'):
                            link = s.get('href')

                        self.general_info['additional_info'].append({'title': title, 'link': 'http://sitl.diputados.gob.mx/LXI_leg/' + str(link)})
            elif x == 2:
                i = 0
                ii = 1
                information = []
                for tds in table.css('td'):
                    text = tds.css('td[width="190"]').extract()
                    if len(text) > 0:
                        soup = bs(text[0])
                        for s in soup.find_all('td'):
                            txt = s.text
                            txt = txt.replace('\t', '')
                            txt = txt.replace('\n', '')
                            txt = txt.strip().lstrip().rstrip()
                            
                            if ii == 1:
                                information.append(txt)
                                ii+=1
                            elif ii == 2:
                                information.append(txt)
                                #print information
                                self.general_info['basic_info'][information[0]] = information[1]
                                information = []
                                ii = 1

                            #print txt

                            #if len(txt) == 2:
                            #    general_info['basic_info'][txt[0].strip()] = txt[1].strip()
                        
                    text = tds.css('td[width="380"]').extract()
                    if len(text) > 0:
                        soup = bs(text[0])
                        for s in soup.find_all('td'):
                            txt = s.text
                            txt = txt.replace('\t', '')
                            txt = txt.replace('\n', '')
                            txt = txt.strip().lstrip().rstrip()
                            txt = txt.split(':')
                            if len(txt) == 2:
                                self.general_info['basic_info'][txt[0].strip()] = txt[1].strip()
                        
                    '''
                    print i
                    if len(text) > 0:
                        if i == 0:
                            soup = bs(text[0])
                            img = None
                            for s in soup.find_all('img'):
                                img = 'http://sitl.diputados.gob.mx/LXI_leg/' + s.get('src')[2:]
                            
                            print img
                        elif i == 1:
                            print
                            #print text[0]
                        elif i == 2:
                            soup = bs(text[0])
                            for i in soup.find_all('span'):
                                title = i.text
                                print title.strip()
                        else i > 2:
                            if ii == 1:

                                ii+=1
                            if ii == 2:

                                ii = 0

                            ii+=1
                            
                    '''
                    i+=1
                    
            '''
            elif x == 3:
                print 'ee'
            '''
            x+=1

        yield self.general_info
        self.general_info = {'additional_info': [], 'basic_info': {}}
            
        
        '''
        for sel in response.xpath('//ul/li'):
            item = DmozItem()
            item['title'] = sel.xpath('a/text()').extract()
            item['link'] = sel.xpath('a/@href').extract()
            item['desc'] = sel.xpath('text()').extract()
            yield item

        '''

            # for rows in table.xpath('//tr'):
                
            #     extracted = rows.select("//a[@class='linkVerde']/text()").extract()

            #     if extracted:
            #         yield {
            #             'name': extracted,
            #         }
            #         break
                #for r in rows.css('a.linkVerde'):
                    #print r.extract_first()
                # #print rows.xpath('//td[class="linkVerde"]//@href').extract()
                # #print rows.xpath('//td[re:test(@class, "linkVerde")]//@href').extract()
                # #sel.xpath('//li[re:test(@class, "item-\d$")]//@href').extract()
                # yield {
                #     'name': rows.xpath('//a/text()').extract(),
                # }
                

                

                
            
