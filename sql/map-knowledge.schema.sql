--
-- PostgreSQL database dump
--

-- Dumped from database version 11.7
-- Dumped by pg_dump version 17.0

-- Started on 2025-04-08 12:12:29 NZST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

--
-- TOC entry 196 (class 1259 OID 26828)
-- Name: alternative_terms; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.alternative_terms (
    term_id character varying NOT NULL,
    alternative character varying NOT NULL
);


ALTER TABLE public.alternative_terms OWNER TO abi;

--
-- TOC entry 204 (class 1259 OID 26928)
-- Name: anatomical_types; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.anatomical_types (
    type_id character varying NOT NULL,
    label text NOT NULL,
    description text
);


ALTER TABLE public.anatomical_types OWNER TO abi;

--
-- TOC entry 206 (class 1259 OID 26984)
-- Name: connectivity_node_features; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_node_features (
    node_id character varying NOT NULL,
    feature_id character varying NOT NULL
);


ALTER TABLE public.connectivity_node_features OWNER TO abi;

--
-- TOC entry 208 (class 1259 OID 27049)
-- Name: connectivity_node_types; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_node_types (
    node_id character varying NOT NULL,
    type_id character varying NOT NULL,
    path_id character varying NOT NULL
);


ALTER TABLE public.connectivity_node_types OWNER TO abi;

--
-- TOC entry 205 (class 1259 OID 26966)
-- Name: connectivity_nodes; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_nodes (
    node_id character varying NOT NULL,
    label text
);


ALTER TABLE public.connectivity_nodes OWNER TO abi;

--
-- TOC entry 201 (class 1259 OID 26880)
-- Name: connectivity_path_edges; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_path_edges (
    path_id character varying NOT NULL,
    node_0 character varying NOT NULL,
    node_1 character varying NOT NULL
);


ALTER TABLE public.connectivity_path_edges OWNER TO abi;

--
-- TOC entry 200 (class 1259 OID 26864)
-- Name: connectivity_path_features; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_path_features (
    path_id character varying NOT NULL,
    feature_id character varying NOT NULL
);


ALTER TABLE public.connectivity_path_features OWNER TO abi;

--
-- TOC entry 212 (class 1259 OID 27168)
-- Name: connectivity_path_phenotypes; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_path_phenotypes (
    path_id character varying NOT NULL,
    phenotype character varying NOT NULL
);


ALTER TABLE public.connectivity_path_phenotypes OWNER TO abi;

--
-- TOC entry 211 (class 1259 OID 27155)
-- Name: connectivity_path_properties; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_path_properties (
    path_id character varying NOT NULL,
    biological_sex character varying,
    alert text,
    disconnected boolean DEFAULT false NOT NULL
);


ALTER TABLE public.connectivity_path_properties OWNER TO abi;

--
-- TOC entry 210 (class 1259 OID 27139)
-- Name: connectivity_path_taxons; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.connectivity_path_taxons (
    path_id character varying NOT NULL,
    taxon_id character varying NOT NULL
);


ALTER TABLE public.connectivity_path_taxons OWNER TO abi;

--
-- TOC entry 199 (class 1259 OID 26848)
-- Name: evidence; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.evidence (
    evidence_id character varying NOT NULL,
    type character varying,
    details text
);


ALTER TABLE public.evidence OWNER TO abi;

--
-- TOC entry 198 (class 1259 OID 26842)
-- Name: feature_evidence; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.feature_evidence (
    term_id character varying NOT NULL,
    evidence_id character varying NOT NULL
);


ALTER TABLE public.feature_evidence OWNER TO abi;

--
-- TOC entry 202 (class 1259 OID 26901)
-- Name: feature_relationship; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.feature_relationship (
    feature_0 character varying NOT NULL,
    feature_1 character varying NOT NULL,
    relationship character varying NOT NULL
);


ALTER TABLE public.feature_relationship OWNER TO abi;

--
-- TOC entry 197 (class 1259 OID 26834)
-- Name: feature_terms; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.feature_terms (
    term_id character varying NOT NULL,
    label text,
    source_id character varying,
    description text
);


ALTER TABLE public.feature_terms OWNER TO abi;

--
-- TOC entry 203 (class 1259 OID 26922)
-- Name: feature_types; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.feature_types (
    term_id character varying NOT NULL,
    type_id character varying NOT NULL
);


ALTER TABLE public.feature_types OWNER TO abi;

--
-- TOC entry 207 (class 1259 OID 27020)
-- Name: knowledge_sources; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.knowledge_sources (
    source_id character varying NOT NULL,
    description text
);


ALTER TABLE public.knowledge_sources OWNER TO abi;

--
-- TOC entry 209 (class 1259 OID 27131)
-- Name: taxons; Type: TABLE; Schema: public; Owner: abi
--

CREATE TABLE public.taxons (
    taxon_id character varying NOT NULL,
    description text
);


ALTER TABLE public.taxons OWNER TO abi;

--
-- TOC entry 3275 (class 2606 OID 26935)
-- Name: anatomical_types anatomical_types_pkey; Type: CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.anatomical_types
    ADD CONSTRAINT anatomical_types_pkey PRIMARY KEY (type_id);


--
-- TOC entry 3269 (class 2606 OID 26855)
-- Name: evidence evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.evidence
    ADD CONSTRAINT evidence_pkey PRIMARY KEY (evidence_id);


--
-- TOC entry 3267 (class 2606 OID 26841)
-- Name: feature_terms features_pkey; Type: CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_terms
    ADD CONSTRAINT features_pkey PRIMARY KEY (term_id);


--
-- TOC entry 3279 (class 2606 OID 27027)
-- Name: knowledge_sources knowledge_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.knowledge_sources
    ADD CONSTRAINT knowledge_sources_pkey PRIMARY KEY (source_id);


--
-- TOC entry 3277 (class 2606 OID 27106)
-- Name: connectivity_nodes node_pkey; Type: CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_nodes
    ADD CONSTRAINT node_pkey PRIMARY KEY (node_id);


--
-- TOC entry 3283 (class 2606 OID 27138)
-- Name: taxons taxons_pkey; Type: CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.taxons
    ADD CONSTRAINT taxons_pkey PRIMARY KEY (taxon_id);


--
-- TOC entry 3270 (class 1259 OID 27112)
-- Name: fki_node_0_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_node_0_constraint ON public.connectivity_path_edges USING btree (node_0);


--
-- TOC entry 3271 (class 1259 OID 27118)
-- Name: fki_node_1_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_node_1_constraint ON public.connectivity_path_edges USING btree (node_1);


--
-- TOC entry 3280 (class 1259 OID 27124)
-- Name: fki_node_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_node_constraint ON public.connectivity_node_types USING btree (node_id);


--
-- TOC entry 3284 (class 1259 OID 27167)
-- Name: fki_path_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_path_constraint ON public.connectivity_path_properties USING btree (path_id);


--
-- TOC entry 3272 (class 1259 OID 27093)
-- Name: fki_path_node_0_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_path_node_0_constraint ON public.connectivity_path_edges USING btree (path_id, node_0);


--
-- TOC entry 3273 (class 1259 OID 27099)
-- Name: fki_path_node_1_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_path_node_1_constraint ON public.connectivity_path_edges USING btree (path_id, node_1);


--
-- TOC entry 3281 (class 1259 OID 27070)
-- Name: fki_path_node_constraint; Type: INDEX; Schema: public; Owner: abi
--

CREATE INDEX fki_path_node_constraint ON public.connectivity_node_types USING btree (node_id, path_id);


--
-- TOC entry 3285 (class 2606 OID 26946)
-- Name: alternative_terms alternative_term_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.alternative_terms
    ADD CONSTRAINT alternative_term_constraint FOREIGN KEY (term_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3287 (class 2606 OID 26956)
-- Name: feature_evidence evidence_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_evidence
    ADD CONSTRAINT evidence_constraint FOREIGN KEY (evidence_id) REFERENCES public.evidence(evidence_id) NOT VALID;


--
-- TOC entry 3294 (class 2606 OID 26907)
-- Name: feature_relationship feature_0_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_relationship
    ADD CONSTRAINT feature_0_constraint FOREIGN KEY (feature_0) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3295 (class 2606 OID 26912)
-- Name: feature_relationship feature_1_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_relationship
    ADD CONSTRAINT feature_1_constraint FOREIGN KEY (feature_1) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3289 (class 2606 OID 26875)
-- Name: connectivity_path_features feature_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_features
    ADD CONSTRAINT feature_constraint FOREIGN KEY (feature_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3296 (class 2606 OID 26936)
-- Name: feature_types feature_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_types
    ADD CONSTRAINT feature_constraint FOREIGN KEY (term_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3288 (class 2606 OID 26951)
-- Name: feature_evidence feature_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_evidence
    ADD CONSTRAINT feature_constraint FOREIGN KEY (term_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3298 (class 2606 OID 26995)
-- Name: connectivity_node_features feature_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_node_features
    ADD CONSTRAINT feature_constraint FOREIGN KEY (feature_id) REFERENCES public.feature_terms(term_id);


--
-- TOC entry 3291 (class 2606 OID 27107)
-- Name: connectivity_path_edges node_0_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_edges
    ADD CONSTRAINT node_0_constraint FOREIGN KEY (node_0) REFERENCES public.connectivity_nodes(node_id) NOT VALID;


--
-- TOC entry 3292 (class 2606 OID 27113)
-- Name: connectivity_path_edges node_1_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_edges
    ADD CONSTRAINT node_1_constraint FOREIGN KEY (node_1) REFERENCES public.connectivity_nodes(node_id) NOT VALID;


--
-- TOC entry 3300 (class 2606 OID 27119)
-- Name: connectivity_node_types node_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_node_types
    ADD CONSTRAINT node_constraint FOREIGN KEY (node_id) REFERENCES public.connectivity_nodes(node_id) NOT VALID;


--
-- TOC entry 3299 (class 2606 OID 27125)
-- Name: connectivity_node_features node_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_node_features
    ADD CONSTRAINT node_constraint FOREIGN KEY (node_id) REFERENCES public.connectivity_nodes(node_id) NOT VALID;


--
-- TOC entry 3293 (class 2606 OID 26917)
-- Name: connectivity_path_edges path_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_edges
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3290 (class 2606 OID 26961)
-- Name: connectivity_path_features path_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_features
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3301 (class 2606 OID 27055)
-- Name: connectivity_node_types path_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_node_types
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id);


--
-- TOC entry 3303 (class 2606 OID 27145)
-- Name: connectivity_path_taxons path_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_taxons
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id);


--
-- TOC entry 3305 (class 2606 OID 27162)
-- Name: connectivity_path_properties path_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_properties
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id) NOT VALID;


--
-- TOC entry 3306 (class 2606 OID 27174)
-- Name: connectivity_path_phenotypes path_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_phenotypes
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id);


--
-- TOC entry 3286 (class 2606 OID 27028)
-- Name: feature_terms source_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_terms
    ADD CONSTRAINT source_constraint FOREIGN KEY (source_id) REFERENCES public.knowledge_sources(source_id) NOT VALID;


--
-- TOC entry 3304 (class 2606 OID 27150)
-- Name: connectivity_path_taxons taxon_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_path_taxons
    ADD CONSTRAINT taxon_constraint FOREIGN KEY (taxon_id) REFERENCES public.taxons(taxon_id);


--
-- TOC entry 3297 (class 2606 OID 26941)
-- Name: feature_types type_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.feature_types
    ADD CONSTRAINT type_constraint FOREIGN KEY (type_id) REFERENCES public.anatomical_types(type_id) NOT VALID;


--
-- TOC entry 3302 (class 2606 OID 27065)
-- Name: connectivity_node_types type_constraint; Type: FK CONSTRAINT; Schema: public; Owner: abi
--

ALTER TABLE ONLY public.connectivity_node_types
    ADD CONSTRAINT type_constraint FOREIGN KEY (type_id) REFERENCES public.anatomical_types(type_id);


-- Completed on 2025-04-08 12:12:31 NZST

--
-- PostgreSQL database dump complete
--

