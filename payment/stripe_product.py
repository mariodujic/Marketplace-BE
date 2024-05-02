from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class StripeProduct:
    id: str
    object: str
    active: bool
    created: int
    default_price: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    livemode: bool = False
    attributes: List[str] = field(default_factory=list)
    marketing_features: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    name: str = ""
    package_dimensions: Optional[dict] = None
    shippable: Optional[bool] = None
    statement_descriptor: Optional[str] = None
    tax_code: Optional[str] = None
    unit_label: Optional[str] = None
    type: Optional[str] = None
    updated: int = 0
    url: Optional[str] = None
