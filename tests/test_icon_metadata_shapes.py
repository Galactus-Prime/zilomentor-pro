"""Isolated legacy icon metadata regression; not a WordPress integration test.
Run: python3 tests/test_icon_metadata_shapes.py /path/to/php
No live files, network, WordPress database or external fonts are used.
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import tempfile

PHP_TEST = "<?php\nnamespace ElementorPro\\Core {\n\tclass Utils {\n\t\tpublic static function _unstable_file_get_contents($p) { return file_get_contents($p); }\n\t\tpublic static function get_ensure_upload_dir($p) { if (!is_dir($p)) mkdir($p,0700,true); return $p; }\n\t}\n}\nnamespace {\ndefine('ABSPATH',__DIR__);\nclass WP_Error { public function __construct(...$args) {} }\nfunction esc_html__($s,$d){return $s;}\nfunction wp_upload_dir(){return ['basedir'=>__DIR__.'/public','baseurl'=>'https://qa.invalid'];}\nfunction apply_filters($n,$v){return $v;}\nfunction trailingslashit($p){return rtrim($p,'/').'/';}\nset_error_handler(static function($n,$s){throw new \\ErrorException($s,0,$n);});\nforeach (['icon-set-base','fontello','icomoon'] as $f) require __DIR__.'/'.$f.'.php';\n$checks=0; $fail=0;\nfunction check($n,$f){global $checks,$fail; $checks++; try {$ok=$f()===true;}catch(\\Throwable $e){$ok=false;echo ' ('.get_class($e).': '.$e->getMessage().') ';} if(!$ok)$fail++;echo ($ok?'PASS ':'FAIL ').$n.PHP_EOL;}\n$ns='ElementorPro\\\\Modules\\\\AssetsManager\\\\AssetTypes\\\\Icons\\\\IconSets\\\\';\n$root=__DIR__.'/fixture/';mkdir($root.'css',0700,true);mkdir($root.'font');mkdir($root.'fonts');mkdir($root.'demo-files');\nforeach(['demo.html','README.txt','LICENSE.txt','Read Mw.txt'] as $f)file_put_contents($root.$f,'test');\n$font=['name'=>'','css_prefix_text'=>'icon-','glyphs'=>[['css'=>'star']]];\n$ico=['metadata'=>['name'=>''],'preferences'=>['fontPref'=>['prefix'=>'icon-','classSelector'=>'.icon']],'icons'=>[['properties'=>['name'=>'star']]]];\nfunction put($p,$data){file_put_contents($p,json_encode($data));}\nfile_put_contents($root.'css/fontello.css','.icon-star:before{content:\"x\"}');\nfile_put_contents($root.'style.css','.icon-star:before{content:\"x\"}');\nforeach(['Fontello'=>[$font,'config.json','glyphs','css/fontello.css'],'Icomoon'=>[$ico,'selection.json','icons','style.css']] as $name=>$values){\n[$config,$file,$field,$css]=$values;$class=$ns.$name;\nput($root.$file,$config);\ncheck($name.' valid legacy config',fn()=>true===(new $class($root))->validate_icon_contents());\nforeach(['scalar list'=>7,'object list'=>['named'=>['css'=>'star']],'null entry'=>[null],'malformed entry'=>[[]]] as $label=>$bad){\n$c=$config;$c[$field]=$bad;put($root.$file,$c);\ncheck($name.' rejects '.$label,fn()=>(new $class($root))->validate_icon_contents() instanceof WP_Error);\n}\n$c=$config;if($name==='Fontello')$c['name']=[];else $c['metadata']['name']=[];\nput($root.$file,$c);\ncheck($name.' rejects nonstring name',fn()=>(new $class($root))->validate_name() instanceof WP_Error);\nput($root.$file,$config);unlink($root.$css);\ncheck($name.' rejects missing CSS',fn()=>(new $class($root))->validate_icon_contents() instanceof WP_Error);\nif($name==='Fontello')check('Fontello prepare does not recreate missing CSS',function()use($class,$root,$css){(new $class($root))->handle_new_icon_set();return !file_exists($root.$css);});\nfile_put_contents($root.$css,'.icon-star:before{content:\"x\"}');\n}\n$c=$ico;$c['preferences']['fontPref']['classSelector']=(object)['bad'=>true];put($root.'selection.json',$c);\ncheck('IcoMoon malformed classSelector does not throw',function()use($ns,$root){$o=new ($ns.'Icomoon')($root);$m=new ReflectionMethod($o,'get_display_prefix');return false===$m->invoke($o);});\necho \"$checks checks; $fail failures\\n\";exit($fail||$checks!==16?1:0);\n}"


def main(root, php, docker_image=None):
    source = root / "modules/assets-manager/asset-types/icons/icon-sets/"
    with tempfile.TemporaryDirectory(prefix="zmp-icon-metadata-") as tmp:
        target = pathlib.Path(tmp)
        for name in ("icon-set-base", "fontello", "icomoon"):
            path = target / (name + ".php")
            shutil.copyfile(source / path.name, path)
            if not docker_image:
                subprocess.run([php, "-l", str(path)], check=True)
        fixture = target / "test.php"
        fixture.write_text(PHP_TEST, encoding="utf-8")
        if docker_image:
            subprocess.run([
                "docker", "run", "--rm", "--pull=never", "--network", "none",
                "--memory", "128m", "--cpus", "1",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "--mount", f"type=bind,src={target},dst=/fixture",
                "--entrypoint", "php", docker_image, "-n", "/fixture/test.php",
            ], check=True)
        else:
            subprocess.run([php, str(fixture)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("php", nargs="?", default="php")
    parser.add_argument("--docker-image", help="Run in an existing local PHP image without network access.")
    args = parser.parse_args()
    main(pathlib.Path(__file__).resolve().parents[1], args.php, args.docker_image)
