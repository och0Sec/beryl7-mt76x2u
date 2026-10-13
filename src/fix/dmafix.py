# Finish MTK's page_pool revert in dma.c for the hunks that did not apply (PCI-only code paths)
p='/build/mt76.b/dma.c'; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:40]); s=s.replace(a,b)
rep("""		dma_sync_single_for_cpu(dev->dma_dev, e->dma_addr[0],
				SKB_WITH_OVERHEAD(q->buf_size),
				page_pool_get_dma_dir(q->page_pool));""","""		dma_unmap_single(dev->dma_dev, e->dma_addr[0],
				 SKB_WITH_OVERHEAD(q->buf_size),
				 DMA_FROM_DEVICE);""")
rep("""		enum dma_data_direction dir;
		struct mt76_queue_buf qbuf;
		dma_addr_t addr;
		int offset;
		void *buf;

		buf = mt76_get_page_pool_buf(q, &offset, q->buf_size);
		if (!buf)
			break;

		addr = page_pool_get_dma_addr(virt_to_head_page(buf)) + offset;
		dir = page_pool_get_dma_dir(q->page_pool);
		dma_sync_single_for_device(dev->dma_dev, addr, len, dir);

		qbuf.addr = addr + q->buf_offset;
		qbuf.len = len - q->buf_offset;
		qbuf.skip_unmap = false;
		if (mt76_dma_add_rx_buf(dev, q, &qbuf, buf) < 0) {
			mt76_put_page_pool_buf(buf, allow_direct);
			break;
		}""","""		struct mt76_queue_buf qbuf;
		void *buf;

		buf = page_frag_alloc(&q->rx_page, q->buf_size, GFP_ATOMIC);
		if (!buf)
			break;

		addr = dma_map_single(dev->dma_dev, buf, len, DMA_FROM_DEVICE);
		if (unlikely(dma_mapping_error(dev->dma_dev, addr))) {
			skb_free_frag(buf);
			break;
		}

		qbuf.addr = addr + offset;
		qbuf.len = len - offset;
		qbuf.skip_unmap = false;
		if (mt76_dma_add_rx_buf(dev, q, &qbuf, buf) < 0) {
			dma_unmap_single(dev->dma_dev, addr, len,
					 DMA_FROM_DEVICE);
			skb_free_frag(buf);
			break;
		}""")
rep("mt76_dma_rx_fill(dev, q, false);","mt76_dma_rx_fill(dev, q);")
rep("		mt76_put_page_pool_buf(buf, false);\n	} while (1);","		skb_free_frag(buf);\n	} while (1);")
open(p,'w').write(s)
