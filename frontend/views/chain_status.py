"""Tab 4: On-Chain-Status — Netzwerk, Contract, Registry-Bestand."""

import streamlit as st

import chain
from ui import components as ui


def render(state: dict) -> None:
    st.header("On-Chain-Status")
    deployment = state["deployment_local"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("RPC-Knoten erreichbar", "Ja" if state["connected"] else "Nein")
        st.metric("ABI kompiliert", "Ja" if state["abi_available"] else "Nein")
    with col2:
        st.metric("Netzwerk", deployment.get("network", "—"))
        st.metric("RPC-URL", state["rpc"])

    address = state["address"] or deployment.get("contractAddress")
    st.markdown('<div class="cp-kv">Contract-Adresse</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div>{ui.hash_html(address or '(unbekannt)')}</div>", unsafe_allow_html=True
    )
    with st.expander("Adresse kopieren"):
        st.code(address or "(unbekannt)", language="text")

    explorer_url = deployment.get("explorerUrl")
    if explorer_url:
        st.link_button("Contract im Explorer öffnen", explorer_url)
    else:
        st.caption("Lokales Netzwerk — kein Block-Explorer verfügbar.")

    if not state["abi_available"]:
        st.error(
            "Contract-ABI fehlt. Einmalig kompilieren (in contracts/): "
            "npm install && npx hardhat compile."
        )
    if not state["connected"] and state["error"]:
        st.error(state["error"])

    if state["connected"]:
        try:
            with st.spinner("Lese Chain-Daten…"):
                info = chain.chain_info(state["web3"])
                records = chain.list_records(state["contract"])
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Chain-ID", info["chainId"])
            col_b.metric("Block", info["blockNumber"])
            col_c.metric("Registrierungen gesamt", records["total"])
            if records["ids"]:
                st.write("**Alle Record-IDs:**")
                st.dataframe(
                    [{"recordId": rid} for rid in records["ids"]],
                    hide_index=True,
                    use_container_width=True,
                )
        except Exception as exc:  # Lesefehler nicht als Stacktrace zeigen
            st.error(f"On-chain-Lesefehler: {exc}")

    if state["last_reg"]:
        st.subheader("Letzte Registrierung (lokal protokolliert)")
        st.dataframe(
            [{"Feld": k, "Wert": str(v)} for k, v in state["last_reg"].items()],
            hide_index=True,
            use_container_width=True,
        )
