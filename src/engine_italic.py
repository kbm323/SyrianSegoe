import fontforge
import sys
import os
import gc

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

print("\n[Italic Engine] Starting Stabilized Grid-Sync Italic Builder...")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Glyphs that Windows needs in system fonts (essential for Windows functionality)
ESSENTIAL_GLYPHS = {
    *range(0x0020, 0x007F),
    *range(0x0100, 0x0250),
    *range(0x1E00, 0x1EFF),
    *range(0x2000, 0x2070),
    *range(0x2070, 0x209F),
    *range(0x20A0, 0x20D0),
    *range(0x2100, 0x214F),
    *range(0x2150, 0x218F),
    *range(0x2190, 0x2200),
    *range(0x2200, 0x2300),
    *range(0x2300, 0x2400),
    *range(0x2500, 0x257F),
    *range(0x2580, 0x259F),
    *range(0x25A0, 0x2600),
    *range(0x2600, 0x2700),
    *range(0x2700, 0x27BF),
    *range(0x0370, 0x0400),
    *range(0x0400, 0x0500),
    *range(0x0590, 0x0600),
    *range(0x0600, 0x0700),
    *range(0x0750, 0x0780),
    *range(0x08A0, 0x0900),
    *range(0xFB50, 0xFE00),
    *range(0xFE70, 0xFF00),
    *range(0x3040, 0x30A0),
    *range(0x3130, 0x3190),
    *range(0x4E00, 0x4FFF),
}


def get_segoe_metrics(segoe_path):
    f = fontforge.open(segoe_path)
    metrics = {
        'em': f.em,
        'ascent': f.ascent,
        'descent': f.descent,
        'hhea_ascent': f.hhea_ascent,
        'hhea_descent': f.hhea_descent,
        'hhea_linegap': f.hhea_linegap,
        'os2_typoascent': f.os2_typoascent,
        'os2_typodescent': f.os2_typodescent,
        'os2_winascent': f.os2_winascent,
        'os2_windescent': f.os2_windescent
    }
    
    # الحصول على الارتفاعات البصرية المرجعية للخطوط المائلة
    try:
        # لاتيني: H
        glyph_h = f[0x48]
        bbox = glyph_h.boundingBox()
        metrics['lat_ref_h'] = bbox[3] - bbox[1]
    except: metrics['lat_ref_h'] = f.ascent * 0.65

    try:
        # عربي: ألف
        glyph_a = f[0x0627]
        bbox = glyph_a.boundingBox()
        metrics['ara_ref_h'] = bbox[3] - bbox[1]
    except: metrics['ara_ref_h'] = f.ascent * 0.65

    f.close()
    return metrics

def cleanup_unused_glyphs(font, preserve_arabic_joining=False, remove_kern_lookups=True):
    try:
        try:
            if remove_kern_lookups and not preserve_arabic_joining:
                for lookup in list(font.gpos_lookups):
                    if 'kern' in lookup.lower():
                        try:
                            font.removeLookup(lookup)
                        except:
                            pass
                print(f"     -> Removed only kern GPOS lookups")
            elif remove_kern_lookups and preserve_arabic_joining:
                print(f"     -> Preserved Arabic GPOS and skipped kern cleanup")
            else:
                print(f"     -> Skipped kern lookup cleanup")
        except Exception as e:
            print(f"     -> Warning managing kern lookups: {e}")
        
        if not preserve_arabic_joining:
            try:
                for lookup in list(font.gsub_lookups):
                    try:
                        font.removeLookup(lookup)
                    except:
                        pass
                print(f"     -> Removed GSUB lookups for non-Arabic cleanup")
            except Exception as e:
                print(f"     -> Warning removing GSUB lookups: {e}")
        
        problematic_glyphs = {
            'uni0300', 'uni0301', 'uni0302', 'uni0303', 'uni0304', 'uni0305', 'uni0306', 'uni0307',
            'uni0308', 'uni0309', 'uni030A', 'uni030B', 'uni030C', 'uni030D', 'uni030E', 'uni030F',
            'uni0310', 'uni0311', 'uni0312', 'uni0313', 'uni0314', 'uni0315', 'uni0316', 'uni0317',
            'uni0318', 'uni0319', 'uni031A', 'uni031B', 'uni031C', 'uni031D', 'uni031E', 'uni031F',
            'uni0330', 'uni0331', 'uni0332', 'uni0333', 'uni0334', 'uni0335', 'uni0336', 'uni0337',
            'uni200B',
            'uni2060', 'uni2061', 'uni2062', 'uni2063', 'uni2064', 'uni2065', 'uni2066',
            'uni2067', 'uni2068', 'uni2069', 'uni206A', 'uni206B', 'uni206C', 'uni206D', 'uni206E',
            'uni206F', 'uni3164', 'uniF8FF', 'uni101DC8', 'dotbelowcomb', 'alpha',
        }
        
        if not preserve_arabic_joining:
            problematic_glyphs.update({'uni200C', 'uni200D', 'uni200E', 'uni200F'})
        
        glyphs_to_remove = []
        glyph_count = len(font.glyphs())
        for i in range(glyph_count):
            try:
                glyph = font.glyphs()[i]
                glyph_name = glyph.name
                if glyph_name in problematic_glyphs:
                    glyphs_to_remove.append(glyph_name)
                elif glyph_name.startswith('uni') and len(glyph_name) > 3:
                    try:
                        codepoint = int(glyph_name[3:], 16)
                        if codepoint not in ESSENTIAL_GLYPHS and codepoint > 0x1000:
                            glyphs_to_remove.append(glyph_name)
                    except:
                        pass
            except:
                pass
        
        if glyphs_to_remove:
            print(f"     -> Removing {len(glyphs_to_remove)} unused/problematic glyphs...")
            for glyph_name in glyphs_to_remove:
                try:
                    font.removeGlyph(glyph_name)
                except:
                    pass
            
    except Exception as e:
        print(f"     -> Warning during glyph cleanup: {e}")


def cleanup_lookup_tables(font, remove_kern_lookups=True):
    try:
        if not remove_kern_lookups:
            print(f"     -> Skipped lookup cleanup for Arabic-preserved font")
            return
        removed_count = 0
        
        try:
            for lookup in list(font.gpos_lookups):
                if 'kern' in lookup.lower():
                    try:
                        font.removeLookup(lookup)
                        removed_count += 1
                    except:
                        pass
        except:
            pass
        
        if removed_count > 0:
            print(f"     -> Removed {removed_count} kern lookup tables")
            
    except Exception as e:
        print(f"     -> Warning during lookup cleanup: {e}")


def prepare_font(path, target_metrics, suffix, wipe_latin=False, strip_ligatures=False, sync_symbols_only=False, preserve_arabic_joining=False, remove_kern_lookups=True):
    """Safely opens a font, syncs the grid, wipes Latin if needed, and saves it."""
    if path == "NONE" or not os.path.exists(path):
        return None
    
    temp_path = os.path.join(BASE_DIR, f"temp_{suffix}.ttf")
    font = None
    try:
        font = fontforge.open(path)
        
        # مطابقة الشبكة وتصحيح الحجم البصري للخطوط المائلة
        try:
            target_em = target_metrics['em']
            source_em = font.em
            
            # البحث عن المرجع البصري
            ref_h_target = 0
            ref_glyph_code = 0
            
            if 0x48 in font:
                ref_glyph_code = 0x48
                ref_h_target = target_metrics['lat_ref_h']
            elif 0x0627 in font:
                ref_glyph_code = 0x0627
                ref_h_target = target_metrics['ara_ref_h']

            if ref_glyph_code > 0:
                try:
                    glyph = font[ref_glyph_code]
                    bbox = glyph.boundingBox()
                    source_ref_h = bbox[3] - bbox[1]
                    
                    if source_ref_h > 0:
                        scale = ref_h_target / source_ref_h
                        print(f"     -> Visual Normalization (Italic): {source_ref_h:.1f} -> {ref_h_target:.1f} (factor {scale:.4f})")
                        
                        font.selection.all()
                        font.transform(fontforge.psMat.scale(scale, scale))
                        
                        for g in font.glyphs():
                            g.width = int(round(g.width * scale))
                except Exception as e:
                    print(f"     -> Warning during visual scaling: {e}")
            
            # توحيد الشبكة والمقاييس
            font.em = target_em
            font.ascent = target_metrics['ascent']
            font.descent = target_metrics['descent']
        except Exception as e:
            print(f"     -> Warning normalizing grid/EM: {e}")
        
        # 0. CLEANUP: Remove problematic glyphs early to prevent spline/kern errors
        print(f"     -> Cleaning up problematic glyphs in {os.path.basename(path)}...")
        cleanup_unused_glyphs(font, preserve_arabic_joining, remove_kern_lookups)
        
        # 0b. Additional cleanup of any remaining lookups
        try:
            cleanup_lookup_tables(font, remove_kern_lookups)
        except:
            pass
        
        # 1. Auto-Detect & Map (Wiping existing Latin)
        if wipe_latin:
            try:
                print(f"     -> Auto-detecting and clearing Latin slots in {os.path.basename(path)}...")
                font.selection.select(("ranges",), 0x0020, 0x024F)
                font.selection.select(("more", "ranges",), 0x1E00, 0x1EFF)
                font.clear()
            except Exception as e:
                print(f"     -> Error clearing Latin range: {e}")

        # 2. Clear Symbols/Punctuation to "sync" them from Segoe (Latin-only mode)
        if sync_symbols_only:
            try:
                print(f"     -> Clearing potential Arabic leftovers in {os.path.basename(path)} to sync system joining logic...")
                # Clear Arabic ranges only to ensure joining logic from Segoe UI is used correctly without interference
                font.selection.select(("ranges",), 0x0600, 0x06FF) # Arabic
                font.selection.select(("more", "ranges",), 0x0750, 0x077F) # Arabic Supplement
                font.selection.select(("more", "ranges",), 0x08A0, 0x08FF) # Arabic Extended-A
                font.selection.select(("more", "ranges",), 0xFB50, 0xFDFF) # Presentation Forms A
                font.selection.select(("more", "ranges",), 0xFE70, 0xFEFF) # Presentation Forms B

                font.clear()
            except Exception as e:
                print(f"     -> Error clearing Arabic leftovers: {e}")
            
        # 3. Strip ALL GSUB/GPOS Lookups aggressively (but preserve Arabic features when requested)
        if strip_ligatures:
            try:
                if preserve_arabic_joining:
                    print(f"     -> Preserving Arabic GSUB/GPOS lookups from {os.path.basename(path)}...")
                else:
                    print(f"     -> Stripping ALL lookup tables (GSUB/GPOS) from {os.path.basename(path)}...")
                    for lookup in list(font.gsub_lookups):
                        try:
                            font.removeLookup(lookup)
                        except:
                            pass
                    for lookup in list(font.gpos_lookups):
                        try:
                            font.removeLookup(lookup)
                        except:
                            pass
            except Exception as e:
                print(f"     -> Error stripping lookups: {e}")

        try:
            font.generate(temp_path)
        except Exception as e:
            print(f"     -> Warning during font generation: {e}")
            # Try to save anyway
            try:
                font.save(temp_path)
            except Exception as e2:
                print(f"     -> Error saving font: {e2}")
                return None
                
    except Exception as e:
        print(f"     -> Critical error processing {os.path.basename(path)}: {e}")
        return None
    finally:
        if font:
            try:
                font.close()
            except:
                pass
        gc.collect() # استدعاء يدوي للمنظف لضمان تحرير الموارد
        
    return temp_path


def _glyph_bbox_height(f, codepoint):
    try:
        g = f[codepoint]
        if g is None:
            return 0
        bbox = g.boundingBox()
        if not bbox:
            return 0
        return max(0, bbox[3] - bbox[1])
    except Exception:
        return 0


def process_weight(latin_path, arabic_path, weight_type, segoe_filename):
    if latin_path == "NONE": return

    print(f"\n[Engine] Processing {weight_type} weight...")
    segoe_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', segoe_filename)
    
    if not os.path.exists(segoe_path):
        print(f"  -> Error: System {segoe_filename} not found. Skipping...")
        return

    l_temp = None
    a_temp = None
    s_temp = None
    lf = None
    sf = None
    final_font = None
    segoe_meta = None
    
    try:
        # Phase 0: Determine Target Grid
        target_metrics = get_segoe_metrics(segoe_path)
        target_em = target_metrics['em']
        is_latin_only = (arabic_path == "NONE")
        print(f"  -> Syncing to Segoe standard grid ({target_em} EM) and vertical metrics")

        # Phase 1: Prepare Latin (Sync Grid)
        l_temp = prepare_font(latin_path, target_metrics, f"lat_{weight_type}", strip_ligatures=True, sync_symbols_only=is_latin_only)
        if not l_temp:
            print(f"  -> Error: Failed to prepare Latin font. Skipping {weight_type}...")
            return

        # Phase 2: Prepare Arabic (Sync Grid + Wipe Latin)
        a_temp = prepare_font(arabic_path, target_metrics, f"ara_{weight_type}", wipe_latin=True, preserve_arabic_joining=True, strip_ligatures=False, remove_kern_lookups=False)
        if not is_latin_only and not a_temp:
            print(f"  -> Error: Failed to prepare Arabic font. Skipping {weight_type}...")
            return

        # Phase 3: Prepare Segoe Symbols
        s_temp = os.path.join(BASE_DIR, f"temp_sym_{weight_type}.ttf")
        try:
            sf = fontforge.open(segoe_path)

            # Sync Segoe Symbols grid to target_em (Crucial for Latin-only mode)
            if sf.em != target_em:
                sf.em = target_em

            # Wipe Alphanumeric, Basic Punctuation (ASCII), and Arabic from Segoe to prioritize the user's chosen font
            sf.selection.select(("ranges",), 0x0020, 0x007E) # ASCII Range (Punctuation + Alphanumeric)
            sf.selection.select(("more", "ranges",), 0x0600, 0x06FF) # Arabic blocks
            sf.selection.select(("more", "ranges",), 0xFB50, 0xFDFF)
            sf.selection.select(("more", "ranges",), 0xFE70, 0xFEFF)
            sf.clear()

            if not is_latin_only:
                # In dual mode, we strip lookups as they are provided by the chosen Latin/Arabic fonts.
                try:
                    for lookup in list(sf.gsub_lookups):
                        try:
                            sf.removeLookup(lookup)
                        except:
                            pass
                    for lookup in list(sf.gpos_lookups):
                        try:
                            sf.removeLookup(lookup)
                        except:
                            pass
                except Exception as e:
                    print(f"  -> Warning while removing lookups: {e}")
            
            # Always clean Segoe font without removing Arabic GPOS or kern lookups
            try:
                cleanup_unused_glyphs(sf, preserve_arabic_joining=True, remove_kern_lookups=False)
            except:
                pass

            try:
                sf.generate(s_temp)
            except Exception as e:
                print(f"  -> Warning generating Segoe symbols: {e}")
                try:
                    sf.save(s_temp)
                except Exception as e2:
                    print(f"  -> Error saving Segoe symbols: {e2}")
                    
        except Exception as e:
            print(f"  -> Error processing Segoe symbols: {e}")
            return
        finally:
            if sf:
                try:
                    sf.close()
                except:
                    pass
            sf = None
            gc.collect()

        # Phase 4: Final Merge (Assembly Line)
        try:
            print("  -> Assembling final font...")
            if a_temp and os.path.exists(a_temp):
                final_font = fontforge.open(a_temp)
                final_font.mergeFonts(l_temp)
            else:
                final_font = fontforge.open(l_temp)
            
            if os.path.exists(s_temp):
                final_font.mergeFonts(s_temp)
            
        except Exception as e:
            print(f"  -> Error during font merge: {e}")
            if final_font:
                try:
                    final_font.close()
                except:
                    pass
            return

        # Phase 5: Metadata & Windows Metrics
        try:
            segoe_meta = fontforge.open(segoe_path)
            final_font.fontname = segoe_meta.fontname
            final_font.familyname = segoe_meta.familyname
            final_font.fullname = segoe_meta.fullname
            final_font.sfnt_names = segoe_meta.sfnt_names
            final_font.os2_weight = segoe_meta.os2_weight
            final_font.os2_stylemap = segoe_meta.os2_stylemap
            
            # Sync ALL vertical metrics to match segoeui.ttf standard
            final_font.ascent = segoe_meta.ascent
            final_font.descent = segoe_meta.descent
            final_font.hhea_ascent = segoe_meta.hhea_ascent
            final_font.hhea_descent = segoe_meta.hhea_descent
            final_font.hhea_linegap = segoe_meta.hhea_linegap
            final_font.os2_typoascent = segoe_meta.os2_typoascent
            final_font.os2_typodescent = segoe_meta.os2_typodescent
            final_font.os2_winascent = segoe_meta.os2_winascent
            final_font.os2_windescent = segoe_meta.os2_windescent

            final_font.macstyle = segoe_meta.macstyle
            segoe_meta.close()
            segoe_meta = None
            
        except Exception as e:
            print(f"  -> Warning updating metadata: {e}")

        output_name = os.path.join(BASE_DIR, f"{segoe_filename.split('.')[0]}_system_mod.ttf")
        
        try:
            final_font.generate(output_name)
        except Exception as e:
            print(f"  -> Error generating final font: {e}")
            try:
                final_font.save(output_name)
            except Exception as e2:
                print(f"  -> Failed to save final font: {e2}")
                return
                
        print(f"  -> Success! Saved as: {os.path.basename(output_name)}")
        
    except Exception as e:
        print(f"  -> Unexpected error processing {weight_type}: {e}")
        
    finally:
        # Cleanup all open fonts and temp files
        for font_obj in [final_font, lf, sf, segoe_meta]:
            if font_obj:
                try:
                    font_obj.close()
                except:
                    pass
        
        for temp_file in [l_temp, a_temp, s_temp]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        gc.collect()


weights_map = [
    ("Light Italic", sys.argv[1], sys.argv[7], "seguili.ttf"),
    ("Semilight Italic", sys.argv[2], sys.argv[8], "seguisli.ttf"),
    ("Italic", sys.argv[3], sys.argv[9], "segoeuii.ttf"),
    ("Semibold Italic", sys.argv[4], sys.argv[10], "seguisbi.ttf"),
    ("Bold Italic", sys.argv[5], sys.argv[11], "segoeuiz.ttf"),
    ("Black Italic", sys.argv[6], sys.argv[12], "seguibli.ttf")
]

for weight_name, lat_path, ara_path, sys_filename in weights_map:
    process_weight(lat_path, ara_path, weight_name, sys_filename)

print("\n[Italic Engine] All italic replacement fonts built successfully!")
