--------------------------------------------------------------
--
-- PostgreSQL database dump
--

-- Dumped from database version 11.7
-- Dumped by pg_dump version 17.0

-- Started on 2025-04-08 12:12:29 NZST
--------------------------------------------------------------

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

--------------------------------------------------------------

CREATE TABLE public.alternative_terms (
    term_id character varying NOT NULL,
    alternative character varying NOT NULL
);
ALTER TABLE public.alternative_terms OWNER TO abi;

CREATE TABLE public.anatomical_types (
    type_id character varying NOT NULL,
    label text NOT NULL,
    description text
);
ALTER TABLE public.anatomical_types OWNER TO abi;

CREATE TABLE public.connectivity_node_features (
    node_id character varying NOT NULL,
    feature_id character varying NOT NULL
);
ALTER TABLE public.connectivity_node_features OWNER TO abi;

CREATE TABLE public.connectivity_node_types (
    node_id character varying NOT NULL,
    type_id character varying NOT NULL,
    path_id character varying NOT NULL
);
ALTER TABLE public.connectivity_node_types OWNER TO abi;

CREATE TABLE public.connectivity_nodes (
    node_id character varying NOT NULL,
    label text
);
ALTER TABLE public.connectivity_nodes OWNER TO abi;

CREATE TABLE public.connectivity_path_edges (
    path_id character varying NOT NULL,
    node_0 character varying NOT NULL,
    node_1 character varying NOT NULL
);
ALTER TABLE public.connectivity_path_edges OWNER TO abi;

CREATE TABLE public.connectivity_path_features (
    path_id character varying NOT NULL,
    feature_id character varying NOT NULL
);
ALTER TABLE public.connectivity_path_features OWNER TO abi;

CREATE TABLE public.connectivity_path_phenotypes (
    path_id character varying NOT NULL,
    phenotype character varying NOT NULL
);
ALTER TABLE public.connectivity_path_phenotypes OWNER TO abi;

CREATE TABLE public.connectivity_path_properties (
    path_id character varying NOT NULL,
    biological_sex character varying,
    alert text,
    disconnected boolean DEFAULT false NOT NULL
);
ALTER TABLE public.connectivity_path_properties OWNER TO abi;

CREATE TABLE public.connectivity_path_taxons (
    path_id character varying NOT NULL,
    taxon_id character varying NOT NULL
);
ALTER TABLE public.connectivity_path_taxons OWNER TO abi;

CREATE TABLE public.evidence (
    evidence_id character varying NOT NULL,
    type character varying,
    details text
);
ALTER TABLE public.evidence OWNER TO abi;

CREATE TABLE public.feature_evidence (
    term_id character varying NOT NULL,
    evidence_id character varying NOT NULL
);
ALTER TABLE public.feature_evidence OWNER TO abi;

CREATE TABLE public.feature_relationship (
    feature_0 character varying NOT NULL,
    feature_1 character varying NOT NULL,
    relationship character varying NOT NULL
);
ALTER TABLE public.feature_relationship OWNER TO abi;

CREATE TABLE public.feature_terms (
    term_id character varying NOT NULL,
    label text,
    source_id character varying,
    description text
);
ALTER TABLE public.feature_terms OWNER TO abi;

CREATE TABLE public.feature_types (
    term_id character varying NOT NULL,
    type_id character varying NOT NULL
);
ALTER TABLE public.feature_types OWNER TO abi;

CREATE TABLE public.knowledge_sources (
    source_id character varying NOT NULL,
    description text
);
ALTER TABLE public.knowledge_sources OWNER TO abi;

CREATE TABLE public.taxons (
    taxon_id character varying NOT NULL,
    description text
);
ALTER TABLE public.taxons OWNER TO abi;

--------------------------------------------------------------

ALTER TABLE ONLY public.anatomical_types
    ADD CONSTRAINT anatomical_types_pkey PRIMARY KEY (type_id);

ALTER TABLE ONLY public.evidence
    ADD CONSTRAINT evidence_pkey PRIMARY KEY (evidence_id);

ALTER TABLE ONLY public.feature_terms
    ADD CONSTRAINT features_pkey PRIMARY KEY (term_id);

ALTER TABLE ONLY public.knowledge_sources
    ADD CONSTRAINT knowledge_sources_pkey PRIMARY KEY (source_id);

ALTER TABLE ONLY public.connectivity_nodes
    ADD CONSTRAINT node_pkey PRIMARY KEY (node_id);

ALTER TABLE ONLY public.taxons
    ADD CONSTRAINT taxons_pkey PRIMARY KEY (taxon_id);

--------------------------------------------------------------

CREATE INDEX fki_node_0_constraint ON public.connectivity_path_edges USING btree (node_0);
CREATE INDEX fki_node_1_constraint ON public.connectivity_path_edges USING btree (node_1);
CREATE INDEX fki_node_constraint ON public.connectivity_node_types USING btree (node_id);
CREATE INDEX fki_path_constraint ON public.connectivity_path_properties USING btree (path_id);
CREATE INDEX fki_path_node_0_constraint ON public.connectivity_path_edges USING btree (path_id, node_0);
CREATE INDEX fki_path_node_1_constraint ON public.connectivity_path_edges USING btree (path_id, node_1);
CREATE INDEX fki_path_node_constraint ON public.connectivity_node_types USING btree (node_id, path_id);

--------------------------------------------------------------

ALTER TABLE ONLY public.alternative_terms
    ADD CONSTRAINT alternative_term_constraint FOREIGN KEY (term_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.feature_evidence
    ADD CONSTRAINT evidence_constraint FOREIGN KEY (evidence_id) REFERENCES public.evidence(evidence_id) NOT VALID;

ALTER TABLE ONLY public.feature_relationship
    ADD CONSTRAINT feature_0_constraint FOREIGN KEY (feature_0) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.feature_relationship
    ADD CONSTRAINT feature_1_constraint FOREIGN KEY (feature_1) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_path_features
    ADD CONSTRAINT feature_constraint FOREIGN KEY (feature_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.feature_types
    ADD CONSTRAINT feature_constraint FOREIGN KEY (term_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.feature_evidence
    ADD CONSTRAINT feature_constraint FOREIGN KEY (term_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_node_features
    ADD CONSTRAINT feature_constraint FOREIGN KEY (feature_id) REFERENCES public.feature_terms(term_id);
ALTER TABLE ONLY public.connectivity_path_edges
    ADD CONSTRAINT node_0_constraint FOREIGN KEY (node_0) REFERENCES public.connectivity_nodes(node_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_path_edges
    ADD CONSTRAINT node_1_constraint FOREIGN KEY (node_1) REFERENCES public.connectivity_nodes(node_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_node_types
    ADD CONSTRAINT node_constraint FOREIGN KEY (node_id) REFERENCES public.connectivity_nodes(node_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_node_features
    ADD CONSTRAINT node_constraint FOREIGN KEY (node_id) REFERENCES public.connectivity_nodes(node_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_path_edges
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_path_features
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_node_types
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id);
ALTER TABLE ONLY public.connectivity_path_taxons
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id);
ALTER TABLE ONLY public.connectivity_path_properties
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_path_phenotypes
    ADD CONSTRAINT path_constraint FOREIGN KEY (path_id) REFERENCES public.feature_terms(term_id);

ALTER TABLE ONLY public.feature_terms
    ADD CONSTRAINT source_constraint FOREIGN KEY (source_id) REFERENCES public.knowledge_sources(source_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_path_taxons
    ADD CONSTRAINT taxon_constraint FOREIGN KEY (taxon_id) REFERENCES public.taxons(taxon_id);

ALTER TABLE ONLY public.feature_types
    ADD CONSTRAINT type_constraint FOREIGN KEY (type_id) REFERENCES public.anatomical_types(type_id) NOT VALID;

ALTER TABLE ONLY public.connectivity_node_types
    ADD CONSTRAINT type_constraint FOREIGN KEY (type_id) REFERENCES public.anatomical_types(type_id);

--------------------------------------------------------------
