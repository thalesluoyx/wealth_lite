import pytest
from fastapi.testclient import TestClient
from main import WealthLiteApp
from src.wealth_lite.models.enums import AssetType, Currency, TransactionType
from decimal import Decimal
from datetime import date
from src.wealth_lite.services.wealth_service import WealthService
import pathlib

@pytest.fixture(autouse=True)
def patch_path_mkdir(monkeypatch):
    def safe_mkdir(self, *args, **kwargs):
        # 跳过:memory:等特殊路径
        if str(self) in (":memory:", ""):
            return
        return pathlib.Path.__original_mkdir__(self, *args, **kwargs)
    if not hasattr(pathlib.Path, "__original_mkdir__"):
        pathlib.Path.__original_mkdir__ = pathlib.Path.mkdir
    monkeypatch.setattr(pathlib.Path, "mkdir", safe_mkdir)

@pytest.fixture
def app_with_tempfile_db(tmp_path, monkeypatch):
    """使用临时文件数据库启动FastAPI应用"""
    db_file = tmp_path / "test_db.sqlite"
    app_instance = WealthLiteApp()
    app_instance.wealth_service = WealthService(db_path=str(db_file))
    monkeypatch.setattr(app_instance, 'initialize_services', lambda: None)
    app = app_instance.create_app()
    return app

@pytest.fixture
def client(app_with_tempfile_db):
    return TestClient(app_with_tempfile_db)

def test_dashboard_summary(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_assets" in data
    assert "cash_assets" in data
    assert "fixed_income_assets" in data or "fixed_income" in data
    assert "assets" in data

def test_asset_crud_and_validation(client):
    # 1. 正常创建资产
    asset_data = {
        "name": "测试活期账户",
        "type": AssetType.CASH.value,
        "currency": Currency.CNY.value,
        "description": "测试用活期账户"
    }
    resp = client.post("/api/assets", json=asset_data)
    assert resp.status_code == 200
    asset = resp.json()
    assert asset["name"] == "测试活期账户"
    asset_id = asset["id"]

    # 2. 查询资产列表
    resp = client.get("/api/assets")
    assert resp.status_code == 200
    assets = resp.json()
    assert any(a["id"] == asset_id for a in assets)

    # 3. 缺少必填字段
    resp = client.post("/api/assets", json={"type": AssetType.CASH.value, "currency": Currency.CNY.value})
    assert resp.status_code == 400
    assert "缺少必填字段" in resp.json().get("detail", "")

    # 4. 非法类型
    resp = client.post("/api/assets", json={"name": "非法资产", "type": "NOTYPE", "currency": Currency.CNY.value})
    assert resp.status_code == 400
    assert "无效的枚举值" in resp.json().get("detail", "")

    # 5. 多资产创建
    asset2 = {
        "name": "测试定期存款",
        "type": AssetType.FIXED_INCOME.value,
        "currency": Currency.CNY.value,
        "description": "测试用定期存款"
    }
    resp = client.post("/api/assets", json=asset2)
    assert resp.status_code == 200
    resp = client.get("/api/assets")
    assets = resp.json()
    assert len(assets) >= 2

def test_transactions_query(client):
    # 1. 资产先创建
    asset_data = {
        "name": "交易测试账户",
        "type": AssetType.CASH.value,
        "currency": Currency.CNY.value,
        "description": "交易测试"
    }
    resp = client.post("/api/assets", json=asset_data)
    assert resp.status_code == 200
    asset_id = resp.json()["id"]

    # 2. 查询交易列表（目前只能查，不能增删）
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    # 允许为空，但接口必须可用

    # 3. 创建交易（假设API已实现）
    # 这里只做接口结构示例，具体参数需与后端实现一致
    transaction_data = {
        "asset_id": asset_id,
        "type": TransactionType.DEPOSIT.value,
        "amount": 10000.0,
        "currency": Currency.CNY.value,
        "date": date.today().isoformat(),
        "exchange_rate": 1.0,
        "notes": "测试存入"
    }
    # resp = client.post("/api/transactions", json=transaction_data)
    # assert resp.status_code == 200
    # transaction = resp.json()
    # assert transaction["asset_id"] == asset_id

    # 4. 查询交易列表
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    # transactions = resp.json()
    # assert any(t["asset_id"] == asset_id for t in transactions)

    # 5. 查询仪表板
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    dashboard = resp.json()
    assert "total_assets" in dashboard 

def test_asset_delete(client):
    # 创建资产
    asset_data = {
        "name": "待删除资产",
        "type": AssetType.CASH.value,
        "currency": Currency.CNY.value,
        "description": "删除测试"
    }
    resp = client.post("/api/assets", json=asset_data)
    assert resp.status_code == 200
    asset_id = resp.json()["id"]
    # 删除资产
    resp = client.delete(f"/api/assets/{asset_id}")
    assert resp.status_code == 200
    assert resp.json().get("success")
    # 再次删除应404
    resp = client.delete(f"/api/assets/{asset_id}")
    assert resp.status_code == 404

def test_transaction_culd(client):
    # 1. 创建资产
    asset_data = {
        "name": "交易CULD账户",
        "type": AssetType.CASH.value,
        "currency": Currency.CNY.value,
        "description": "交易CULD测试"
    }
    resp = client.post("/api/assets", json=asset_data)
    assert resp.status_code == 200
    asset_id = resp.json()["id"]
    # 2. 创建交易
    tx_data = {
        "asset_id": asset_id,
        "type": TransactionType.DEPOSIT.value,
        "amount": 5000.0,
        "currency": Currency.CNY.value,
        "date": date.today().isoformat(),
        "exchange_rate": 1.0,
        "notes": "初始存入"
    }
    resp = client.post("/api/transactions", json=tx_data)
    assert resp.status_code == 200
    tx = resp.json()
    tx_id = tx["id"]
    assert tx["amount"] == 5000.0
    # 3. 查询交易
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    txs = resp.json()
    assert any(t["id"] == tx_id for t in txs)
    # 4. 更新交易
    update_data = {"amount": 8888.0, "notes": "修改备注"}
    resp = client.put(f"/api/transactions/{tx_id}", json=update_data)
    assert resp.status_code == 200
    # 5. 查询确认更新
    resp = client.get("/api/transactions")
    txs = resp.json()
    updated = [t for t in txs if t["id"] == tx_id][0]
    assert updated["amount"] == 8888.0
    # 6. 删除交易
    resp = client.delete(f"/api/transactions/{tx_id}")
    assert resp.status_code == 200
    # 7. 再次删除应404
    resp = client.delete(f"/api/transactions/{tx_id}")
    assert resp.status_code == 404 