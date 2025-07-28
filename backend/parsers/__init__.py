"""Bank statement parsers module"""

# Import all parsers
from .becu_parser import BECUParser
from .citizens_parser import CitizensParser
from .commonwealth_parser import CommonwealthParser
from .discover_parser import DiscoverParser
from .green_dot_parser import GreenDotParser
from .lloyds_parser import LloydsParser
from .metro_parser import MetroParser
from .nationwide_parser import NationwideParser
from .netspend_parser import NetspendParser
from .paypal_parser import PaypalParser
from .scotiabank_parser import ScotiabankParser
from .suntrust_parser import SuntrustParser
from .walmart_parser import WalmartParser
from .westpac_parser import WestpacParser

# Parser mapping
BANK_PARSERS = {
    'becu': BECUParser,
    'citizens': CitizensParser,
    'commonwealth': CommonwealthParser,
    'discover': DiscoverParser,
    'green_dot': GreenDotParser,
    'lloyds': LloydsParser,
    'metro': MetroParser,
    'nationwide': NationwideParser,
    'netspend': NetspendParser,
    'paypal': PaypalParser,
    'scotiabank': ScotiabankParser,
    'suntrust': SuntrustParser,
    'walmart': WalmartParser,
    'westpac': WestpacParser
}
