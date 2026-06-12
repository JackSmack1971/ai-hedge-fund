from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.backend.database.models import HedgeFundFlow

DEFAULT_TEMPLATE_FLOW_NAME = "Data Wizards"
DEFAULT_TEMPLATE_FLOW_DESCRIPTION = "A starter flow with Portfolio Input, three analysts, and a Portfolio Manager."
DEFAULT_TEMPLATE_FLOW_NODES = [
    {
        "id": "portfolio-start-node_tmpl01",
        "type": "portfolio-start-node",
        "position": {"x": 0, "y": 0},
        "data": {
            "name": "Portfolio Input",
            "description": "Enter your portfolio including tickers, shares, and prices.",
            "status": "Idle",
        },
    },
    {
        "id": "valuation_analyst_tmpl01",
        "type": "agent-node",
        "position": {"x": 360, "y": -220},
        "data": {
            "name": "Valuation Analyst",
            "description": "Company valuation specialist.",
            "status": "Idle",
        },
    },
    {
        "id": "sentiment_analyst_tmpl01",
        "type": "agent-node",
        "position": {"x": 360, "y": 0},
        "data": {
            "name": "Sentiment Analyst",
            "description": "News and market sentiment specialist.",
            "status": "Idle",
        },
    },
    {
        "id": "technical_analyst_tmpl01",
        "type": "agent-node",
        "position": {"x": 360, "y": 220},
        "data": {
            "name": "Technical Analyst",
            "description": "Price action and technical analysis specialist.",
            "status": "Idle",
        },
    },
    {
        "id": "portfolio-manager-node_tmpl01",
        "type": "portfolio-manager-node",
        "position": {"x": 720, "y": 0},
        "data": {
            "name": "Portfolio Manager",
            "description": "Synthesizes analyst signals into a trading decision.",
            "status": "Idle",
        },
    },
]
DEFAULT_TEMPLATE_FLOW_EDGES = [
    {"id": "e-portfolio-start-valuation", "source": "portfolio-start-node_tmpl01", "target": "valuation_analyst_tmpl01"},
    {"id": "e-portfolio-start-sentiment", "source": "portfolio-start-node_tmpl01", "target": "sentiment_analyst_tmpl01"},
    {"id": "e-portfolio-start-technical", "source": "portfolio-start-node_tmpl01", "target": "technical_analyst_tmpl01"},
    {"id": "e-valuation-manager", "source": "valuation_analyst_tmpl01", "target": "portfolio-manager-node_tmpl01"},
    {"id": "e-sentiment-manager", "source": "sentiment_analyst_tmpl01", "target": "portfolio-manager-node_tmpl01"},
    {"id": "e-technical-manager", "source": "technical_analyst_tmpl01", "target": "portfolio-manager-node_tmpl01"},
]


class FlowRepository:
    """Repository for HedgeFundFlow CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_flow(
        self,
        name: str,
        nodes: Dict[str, Any],
        edges: Dict[str, Any],
        description: Optional[str] = None,
        viewport: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_template: bool = False,
        tags: Optional[List[str]] = None,
    ) -> HedgeFundFlow:
        """Create a new hedge fund flow"""
        flow = HedgeFundFlow(
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            viewport=viewport,
            data=data,
            is_template=is_template,
            tags=tags or [],
        )
        self.db.add(flow)
        self.db.commit()
        self.db.refresh(flow)
        return flow

    def get_flow_by_id(self, flow_id: int) -> Optional[HedgeFundFlow]:
        """Get a flow by its ID"""
        return self.db.query(HedgeFundFlow).filter(HedgeFundFlow.id == flow_id).first()

    def get_all_flows(self, include_templates: bool = True) -> List[HedgeFundFlow]:
        """Get all flows, optionally excluding templates"""
        query = self.db.query(HedgeFundFlow)
        if not include_templates:
            query = query.filter(HedgeFundFlow.is_template == False)
        return query.order_by(HedgeFundFlow.updated_at.desc()).all()

    def ensure_default_template_flow(self) -> Optional[HedgeFundFlow]:
        """Seed the starter template flow when the flows table is empty."""
        if self.db.query(HedgeFundFlow).count() > 0:
            return None

        existing_template = self.db.query(HedgeFundFlow).filter(HedgeFundFlow.name == DEFAULT_TEMPLATE_FLOW_NAME).first()
        if existing_template:
            return existing_template

        return self.create_flow(
            name=DEFAULT_TEMPLATE_FLOW_NAME,
            description=DEFAULT_TEMPLATE_FLOW_DESCRIPTION,
            nodes=DEFAULT_TEMPLATE_FLOW_NODES,
            edges=DEFAULT_TEMPLATE_FLOW_EDGES,
            viewport={"x": 0, "y": 0, "zoom": 1},
            data={},
            is_template=True,
            tags=["template", "onboarding", "starter"],
        )

    def get_flows_by_name(self, name: str) -> List[HedgeFundFlow]:
        """Search flows by name (case-insensitive partial match)"""
        return (
            self.db.query(HedgeFundFlow)
            .filter(HedgeFundFlow.name.ilike(f"%{name}%"))
            .order_by(HedgeFundFlow.updated_at.desc())
            .all()
        )

    def update_flow(
        self,
        flow_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[Dict[str, Any]] = None,
        edges: Optional[Dict[str, Any]] = None,
        viewport: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_template: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[HedgeFundFlow]:
        """Update an existing flow"""
        flow = self.get_flow_by_id(flow_id)
        if not flow:
            return None

        if name is not None:
            flow.name = name
        if description is not None:
            flow.description = description
        if nodes is not None:
            flow.nodes = nodes
        if edges is not None:
            flow.edges = edges
        if viewport is not None:
            flow.viewport = viewport
        if data is not None:
            flow.data = data
        if is_template is not None:
            flow.is_template = is_template
        if tags is not None:
            flow.tags = tags

        self.db.commit()
        self.db.refresh(flow)
        return flow

    def delete_flow(self, flow_id: int) -> bool:
        """Delete a flow by ID"""
        flow = self.get_flow_by_id(flow_id)
        if not flow:
            return False

        self.db.delete(flow)
        self.db.commit()
        return True

    def duplicate_flow(self, flow_id: int, new_name: str = None) -> Optional[HedgeFundFlow]:
        """Create a copy of an existing flow"""
        original = self.get_flow_by_id(flow_id)
        if not original:
            return None

        copy_name = new_name or f"{original.name} (Copy)"

        return self.create_flow(
            name=copy_name,
            description=original.description,
            nodes=original.nodes,
            edges=original.edges,
            viewport=original.viewport,
            data=original.data,
            is_template=False,  # Copies are not templates by default
            tags=original.tags,
        )
