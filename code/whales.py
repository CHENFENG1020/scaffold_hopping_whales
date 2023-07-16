import os
# chemistry toolkits
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Draw  # for molecule depiction
# WHALES-related code
import ChemTools as Tools  # for molecule pretreatment
import do_whales  # importing WHALES descriptors
from ChemTools import prepare_mol_from_sdf  # to pretreat the virtual screening library
# for data analysis and plotting
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics.pairwise import euclidean_distances
import numpy
# for running time
import time
from pathlib import Path


# ----------------------------------------------------------------------------------------------------------------------
def run(mol, lib, output_name='out', count_num=0, pick_num=0):
    start = time.clock()
    print('Mission start!')

    output_dir = str(Path.cwd().parent / output_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print('Results will be saved in ' + output_dir)

    print('Preparing reference moleculer...')
    if '.sdf' in mol:
        # imports from sdf
        template = Chem.MolFromMolFile(mol)
        mol, err = Tools.prepare_mol(template, do_geometry=False)  # 准备分子，检查错误，优化结构
        if err == 1:
            print('Reference mol is wrong!')
            exit()
        Tools.do_map(template, fig_name=output_dir + 'partial_charge.png', lab_atom=True)
    else:
        # imports from Smiles
        with open(mol, 'r') as mol:
            mol = mol.readline()
        template = Chem.MolFromSmiles(mol)
        err = AllChem.Compute2DCoords(template)  # 没有错误 err == 0
        if err == 1:
            print('Reference mol is wrong!')
            exit()
        mol, err = Tools.prepare_mol(template)  # 准备分子，检查错误，优化结构
        Tools.do_map(template, fig_name=output_dir + 'partial_charge.png', lab_atom=True)  # 检查用于WHALES的结构 无法展示，直接保存
        writer = Chem.SDWriter(output_dir + 'ref.sdf')  # 创建分子文件
        writer.write(mol)  # 写入分子3D坐标
    # 储存初始与优化后结构
    reference = [template, mol]
    Draw.MolsToGridImage(reference, molsPerRow=2, subImgSize=(500, 500)).save(output_dir + 'reference_vs_opt.png')

    # 准备筛选库
    print('Library address is ' + lib)
    print('Preparing compounds Library...')
    vs_library_with_cnt, num_to_pick, mol_not_computed_1 = prepare_mol_from_sdf(lib, count_num, pick_num)

    '''
    #视觉检查库是否正确
    number_mol = 6  # 检查前六个库中的分子
    Draw.MolsToGridImage(vs_library[:number_mol], molsPerRow=3, subImgSize=(100, 100),
                         legends=[x.GetProp("_Name") for x in vs_library[:number_mol]]).save(output_dir + 'lib_check.png')
    '''

    # ----------------------------------------------------------------------------------------------------------------------
    # 计算参考分子的WHALES
    print('Computing WHALES of the reference...')
    whales_template, lab, err = do_whales.whales_from_mol(mol)  # 描述符矩阵
    if err == 1:
        print('Reference mol is wrong!')
        exit()
    df_whales_template = pd.DataFrame(whales_template.reshape(-1, len(whales_template)), index=['template'],
                                      columns=lab)
    # 矩阵转化为数据库

    # 计算库的WHALES
    print('Computing WHALES of the library...')
    vs_library = []
    whales_library = []
    mol_not_computed_2 = []
    n = 0
    nmol = len(vs_library_with_cnt)
    for cnt, mol in vs_library_with_cnt.items():  # 遍历库并计算whales
        whales_temp, lab, err = do_whales.whales_from_mol(mol, cnt)
        if err == 1:
            mol_not_computed_2.append(mol)
        else:
            vs_library.append(mol)
            whales_library.append(whales_temp)
        n += 1
        if n % 1000 == 0:
            ('Molecule: ' + str(n) + '/' + str(nmol))
    df_whales_library = pd.DataFrame(whales_library, columns=lab)  # 矩阵转化为数据库
    # df_whales_library.head()  # 前五行库预览

    print('Writing wrong molecules...')
    # 输出有误未计算分子
    if mol_not_computed_1 or mol_not_computed_2:
        n = 0
        writer = Chem.SDWriter(output_dir + 'mol_not_computed.sdf')  # 创建分子文件
        if mol_not_computed_1:
            for cnt, mol in mol_not_computed_1.items():
                n += 1
                if mol is None:
                    print('Moleculer ' + str(cnt) + ' cannot be read!')
                else:
                    writer.write(mol)  # 写入分子坐标
        if mol_not_computed_2:
            for mol in mol_not_computed_2:
                n += 1
                writer.write(mol)  # 写入分子坐标
        print('There are ' + str(n) + ' molecules not computed !')

    print('Writing WHALES_before_scaled...')
    # 输出whales数据
    df_whales_template.to_csv(output_dir + 'ref_WHALES_before_scaled.csv')  # 导出参考分子WHALES
    df_whales_library.to_csv(output_dir + 'lib_WHALES_before_scaled.csv')  # 导出库WHALES

    print('Plotting lib_WHALES_before_scaled...')
    # 可视化虚拟筛选库的生WHALES数据
    sns.set(rc={'figure.figsize': (16, 8.27)})  # 设置图大小
    sns.boxplot(data=df_whales_library, linewidth=2)
    plt.savefig(output_dir + 'lib_WHALES_before_scaled.png')
    # plt.show() #如果过程中要看
    plt.close()

    print('Scaling...')
    # scaling库
    aver = df_whales_library.mean()
    sdv = df_whales_library.std()
    df_whales_library_scaled = (df_whales_library - aver) / sdv

    # scaling参考分子
    df_whales_template_scaled = (df_whales_template - aver) / sdv

    print('Writing WHALES_after_scaled...')
    # 导出scaling后库WHALES数据
    df_whales_template_scaled.to_csv(output_dir + 'ref_WHALES_after_scaled.csv')
    df_whales_library_scaled.to_csv(output_dir + 'lib_WHALES_after_scaled.csv')

    print('Plotting lib_WHALES_after_scaled...')
    # 可视化scaling后库WHALES数据
    sns.set(rc={'figure.figsize': (16, 8.27)})
    sns.boxplot(data=df_whales_library_scaled, linewidth=2)
    plt.savefig(output_dir + 'lib_WHALES_after_scaled.png')
    # plt.show() #如果过程中要看
    plt.close()

    # ----------------------------------------------------------------------------------------------------------------------
    # 开始虚拟筛选
    # 相似性计算
    print('Computing euclidean distance...')
    D = euclidean_distances(df_whales_template_scaled, df_whales_library_scaled)  # compute Euclidean distance

    print('finding hits...')
    # 找 hits
    # 根据距离整理
    sort_index = numpy.argsort(D)  # 根据距离加标号
    D_neig = D[:, sort_index]  # 距离排序
    k = num_to_pick  # hits数量
    print('Number of hits: ' + str(k))
    neighbor_ID = sort_index[:, 0:k]  # hits的序号

    print('Preparing hits file...')
    # 命中
    hits = []
    for j in numpy.nditer(neighbor_ID):
        hits.append(vs_library[int(j)])

    # 输出sdf文件
    writer = Chem.SDWriter(output_dir + 'hits.sdf')  # 创建分子文件
    for hit in hits:
        writer.write(hit)  # 写入分子坐标

    print('Plotting best 10 hits...')
    # 可视化结构优化后的hits
    number_mol = 10  # 要看的hits数量
    hits_2D = []
    for mol in hits[:number_mol]:
        AllChem.Compute2DCoords(mol)
        hits_2D.append(mol)

    outcome = Draw.MolsToGridImage(hits_2D[:number_mol], molsPerRow=5, subImgSize=(500, 500),
                                   legends=[x.GetProp("_Name") for x in hits_2D[:number_mol]])
    outcome.save(output_dir + 'hits.png')  # 输出图片
    print('Mission done!')
    end = time.clock()
    print('time_consumed: ' + str(end - start))


    '''
    # ----------------------------------------------------------------------------------------------------------------------
    # 核心
    core = MurckoScaffold.GetScaffoldForMol(template)  # 参考分子骨架
    scaffold_vs = []  # 库骨架列表
    for mol in vs_library_2D:
        scaffold_vs.append(MurckoScaffold.GetScaffoldForMol(mol))  # 每个库骨架加入列表
    
    
    # 预览库骨架
    k = 4  # 数量
    Draw.MolsToGridImage(scaffold_vs[:k], molsPerRow=2, subImgSize=(200, 200),
                         legends=[x.GetProp("_Name") for x in scaffold_vs[:k]]).save(output_dir + 'lib_scaffold.png')
    
    freq_scaffolds_library = Tools.frequent_scaffolds(vs_library_2D)  # 骨架列表，以数量排序
    # 预览库最常见骨架
    k = 4  # 数量
    Draw.MolsToGridImage(freq_scaffolds_library[:k], molsPerRow=2, subImgSize=(200, 200),
                         legends=[x.GetProp("_Name") for x in freq_scaffolds_library[:k]]).save(output_dir + 'freq_lib_scaffold.png')
    
    # 计算常见骨架小分子在库中的比例
    SD_rel = len(freq_scaffolds_library) / len(vs_library) * 100  #
    print(SD_rel)
    
    
    # top hits 骨架
    scaffold_hits = []
    for mol in hits:
        scaffold_hits.append(MurckoScaffold.GetScaffoldForMol(mol))
    # 预览所有hits骨架
    Draw.MolsToGridImage(scaffold_hits[:10], molsPerRow=2, subImgSize=(200, 200),
                         legends=[x.GetProp("_Name") for x in scaffold_hits[:10]]).save(output_dir + 'hits_scaffold.png')
    
    freq_scaffolds_hits = Tools.frequent_scaffolds(hits)  # 骨架列表，数量排序
    # 预览所有hits骨架 但按照数量
    k = len(freq_scaffolds_hits)  # 展示所有骨架
    Draw.MolsToGridImage(freq_scaffolds_hits[:k], molsPerRow=2, subImgSize=(200, 200),
                         legends=[x.GetProp("_Name") for x in freq_scaffolds_hits[:k]]).save(output_dir + 'freq_hits_scaffold.png')
    
    # 计算hits常见骨架在hits骨架总数中的比例
    SD_rel = len(freq_scaffolds_hits) / len(hits) * 100
    print(SD_rel)
    '''
